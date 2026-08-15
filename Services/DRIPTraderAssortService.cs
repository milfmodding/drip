using DRIP.Models;
using DRIP.Utils;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common;
using SPTarkov.Server.Core.Models.Eft.Common.Tables;
using SPTarkov.Server.Core.Models.Spt.Server;
using SPTarkov.Server.Core.Models.Utils;
using SPTarkov.Server.Core.Services;
using SPTarkov.Server.Core.Utils.Cloners;

namespace DRIP.Services;

/// <summary>
/// Puts DRIP's items on sale.
///
/// Two mutually exclusive ways, matching how the corpus actually splits (198 items one way, 76 the other):
///
///   copyOriginalOffers: true  - sell it wherever the original is sold, at whatever the original costs. This is what
///                               makes a retextured 6B2 behave like a real 6B2 - same traders, same barter schemes,
///                               same loyalty levels, same armour plates.
///   copyOriginalOffers: false - sell it at this config's own price and loyalty level, from one trader.
///
/// Deferred until every content pack has loaded so the trader index is built exactly once, and so a later pack's
/// items are treated identically to an earlier pack's.
/// </summary>
[Injectable(InjectionType.Singleton)]
public class DRIPTraderAssortService(
    ISptLogger<DRIPTraderAssortService> logger,
    DatabaseService databaseService,
    ICloner cloner
)
{
    /// <summary>Assorts hang off this pseudo-parent rather than off another item.</summary>
    private const string AssortRoot = "hideout";

    /// <summary>What the 3.x mod used for an unlimited trader stock. Kept for parity.</summary>
    private const int UnlimitedStackCount = 814000;

    private readonly List<PendingOffer> _pending = [];

    /// <summary>An item nothing ended up selling, with the reason, because the two reasons need opposite fixes.</summary>
    public record UnsoldItem(string RelativeName, MongoId BaseTpl, bool GatedByQuest);

    private readonly List<UnsoldItem> _unsold = [];

    /// <summary>
    /// Why each copy-mode item found no seller. Annotation only - the self-check still derives *whether* an item is
    /// sold from the database, never from this list, because a bookkeeping list that has drifted would report success
    /// for an item nothing sells.
    /// </summary>
    public IReadOnlyList<UnsoldItem> Unsold => _unsold;

    private DatabaseTables? _database;

    /// <summary>An item waiting to be put on sale, recorded during content pack loading.</summary>
    private record PendingOffer(
        MongoId NewItemId,
        MongoId BaseTpl,
        MongoId TraderId,
        ContentItemConfig Config,
        string RelativeName);

    /// <summary>
    /// One trader's assort, indexed for lookup rather than repeated scanning.
    /// </summary>
    /// <remarks>
    /// The 3.x implementation scanned every trader's whole item list per DRIP item, and then - for each match -
    /// scanned that same list again to find the offer's children (collection.ts:236-247). That inner scan is the
    /// expensive one: it is quadratic in the trader's assort size and only fires on armour and rigs, which are
    /// exactly the categories with the most assort entries. Both collapse to dictionary lookups here, built once.
    /// </remarks>
    private sealed class TraderAssortIndex
    {
        public required MongoId TraderId { get; init; }
        public required Trader Trader { get; init; }

        /// <summary>Root offers by the template they sell.</summary>
        public required Dictionary<MongoId, List<Item>> RootOffersByTemplate { get; init; }

        /// <summary>Child items by the offer they hang off - armour plates and soft armour, in practice.</summary>
        public required Dictionary<string, List<Item>> ChildrenByParent { get; init; }

        /// <summary>Assort ids that are locked behind a quest, in any state.</summary>
        public required HashSet<MongoId> QuestLockedAssorts { get; init; }
    }

    public void Record(MongoId newItemId, MongoId baseTpl, MongoId traderId, ContentItemConfig config, string relativeName)
    {
        _pending.Add(new PendingOffer(newItemId, baseTpl, traderId, config, relativeName));
    }

    /// <summary>
    /// Puts every recorded item on sale. Call once, after all content packs have loaded.
    /// </summary>
    public void ApplyAll()
    {
        if (_pending.Count == 0)
        {
            return;
        }

        _database ??= databaseService.GetTables();

        var index = BuildIndex();

        var copied = 0;
        var priced = 0;
        var failed = 0;
        var childrenCopied = 0;

        foreach (var pending in _pending)
        {
            try
            {
                if (!_database.Traders.TryGetValue(pending.TraderId, out var destination))
                {
                    logger.Error($"[DRIP] {pending.RelativeName}: trader {pending.TraderId} isn't in the database.");
                    failed++;
                    continue;
                }

                if (pending.Config.ShouldCopyOriginalOffers)
                {
                    copied += CopyOriginalOffers(pending, destination, index, ref childrenCopied);
                }
                else
                {
                    if (AddOwnPricedOffer(pending, destination))
                    {
                        priced++;
                    }
                    else
                    {
                        failed++;
                    }
                }
            }
            catch (Exception ex)
            {
                logger.Error($"[DRIP] {pending.RelativeName}: could not put on sale - {ex.Message}");
                failed++;
            }
        }

        var summary =
            $"[DRIP] Trader offers: {copied} copied from the original items " +
            $"({childrenCopied} fitted parts), {priced} at their own price";

        if (failed > 0)
        {
            logger.Error($"{summary}, {failed} failed.");
        }
        else
        {
            logger.Info($"{summary}.");
        }

        _pending.Clear();
    }

    /// <summary>
    /// Indexes every trader's assort once. DRIP's own traders are excluded as sources - they start empty and we are
    /// appending to them as we go, so reading from them would be both pointless and order-dependent.
    /// </summary>
    private List<TraderAssortIndex> BuildIndex()
    {
        var index = new List<TraderAssortIndex>();

        foreach (var (traderId, trader) in _database!.Traders)
        {
            if (trader.Assort?.Items is null || traderId == DripTraders.Moron || traderId == DripTraders.Georgia)
            {
                continue;
            }

            var rootOffers = new Dictionary<MongoId, List<Item>>();
            var children = new Dictionary<string, List<Item>>();

            foreach (var item in trader.Assort.Items)
            {
                if (item.ParentId == AssortRoot)
                {
                    if (!rootOffers.TryGetValue(item.Template, out var offers))
                    {
                        offers = [];
                        rootOffers[item.Template] = offers;
                    }

                    offers.Add(item);
                }
                else if (item.ParentId is not null)
                {
                    if (!children.TryGetValue(item.ParentId, out var kids))
                    {
                        kids = [];
                        children[item.ParentId] = kids;
                    }

                    kids.Add(item);
                }
            }

            // Every quest-locked assort id, across started/success/fail. The 3.x version looked these up by array
            // index rather than by assort id (collection.ts:213-217), so it never actually matched anything and
            // quest-locked offers were being copied as freely available.
            var questLocked = new HashSet<MongoId>();
            if (trader.QuestAssort is not null)
            {
                foreach (var assortId in trader.QuestAssort.Values.SelectMany(state => state.Keys))
                {
                    questLocked.Add(assortId);
                }
            }

            index.Add(new TraderAssortIndex
            {
                TraderId = traderId,
                Trader = trader,
                RootOffersByTemplate = rootOffers,
                ChildrenByParent = children,
                QuestLockedAssorts = questLocked
            });
        }

        // What the index actually saw, because everything downstream is a consequence of it and none of it is
        // otherwise visible. This exists because two of us spent an evening arguing from static models about why 20
        // items reported "no trader sells this" - a disagreement one log line would have settled, since the answer is
        // entirely determined by how much trader data exists at the moment DRIP runs.
        //
        // Read it as a measurement of load order. Trader stock is not uniformly available: ordinary assorts are
        // loaded eagerly by DatabaseImporter, but Fence's is *generated* during TraderCallbacks, which is after us -
        // so Fence appearing here with zero root offers is expected and correct, not a fault.
        // Both counts, named for what they actually are. Summing each trader's template count is NOT "distinct
        // templates" - a template sold by three traders lands in three of those dictionaries. Calling the sum
        // "distinct" cost an unexplained 222 in an otherwise exact prediction, which is the same mislabelled-
        // population mistake this log line exists to prevent, committed inside the log line itself.
        var pairs = index.Sum(entry => entry.RootOffersByTemplate.Count);
        var distinct = index.SelectMany(entry => entry.RootOffersByTemplate.Keys).Distinct().Count();

        logger.Info(
            $"[DRIP] Trader index: {index.Count} traders, " +
            $"{pairs} trader/template pairs over {distinct} distinct templates, " +
            $"{index.Sum(entry => entry.RootOffersByTemplate.Sum(offers => offers.Value.Count))} root offers, " +
            $"{index.Sum(entry => entry.QuestLockedAssorts.Count)} quest-locked assort ids.");

        var empty = index.Where(entry => entry.RootOffersByTemplate.Count == 0).Select(entry => entry.TraderId).ToList();
        if (empty.Count > 0)
        {
            logger.Info($"[DRIP]   traders with no root offers at this point: {string.Join(", ", empty)}");
        }

        return index;
    }

    /// <summary>
    /// Mirrors every offer of the base item onto the DRIP trader, with its price, loyalty level and children.
    /// </summary>
    /// <returns>How many offers were created.</returns>
    private int CopyOriginalOffers(PendingOffer pending, Trader destination, List<TraderAssortIndex> index, ref int childrenCopied)
    {
        var created = 0;

        foreach (var source in index)
        {
            if (!source.RootOffersByTemplate.TryGetValue(pending.BaseTpl, out var originalOffers))
            {
                continue;
            }

            foreach (var original in originalOffers)
            {
                // A quest-locked offer is not freely available, so copying it would hand players an item the
                // original still gates behind a quest.
                if (source.QuestLockedAssorts.Contains(original.Id))
                {
                    continue;
                }

                var newOffer = cloner.Clone(original);
                newOffer.Id = new MongoId();
                newOffer.Template = pending.NewItemId;

                destination.Assort.Items.Add(newOffer);

                if (source.Trader.Assort!.BarterScheme.TryGetValue(original.Id, out var barter))
                {
                    destination.Assort.BarterScheme[newOffer.Id] = cloner.Clone(barter);
                }

                if (source.Trader.Assort.LoyalLevelItems.TryGetValue(original.Id, out var loyalty))
                {
                    destination.Assort.LoyalLevelItems[newOffer.Id] = loyalty;
                }

                childrenCopied += CopyChildren(source, original, newOffer, destination);

                created++;
            }
        }

        if (created == 0)
        {
            // Two very different reasons, with opposite correct fixes, and they must not be reported as one thing.
            //
            // Gated: the original IS sold, but every offer of it is quest-locked, so copying it would hand players a
            // freely-available retexture of gear the base game gates behind a quest. Declining is correct - it is the
            // 3.x bug at collection.ts:213-217, which matched nothing and leaked quest-gated gear for years. Do NOT
            // "fix" these by giving them their own price; that re-opens the leak deliberately.
            //
            // Nowhere: the original is sold by nobody reachable. In practice that means Fence was its only seller and
            // Fence's assort does not exist at our load priority - and since Fence's generated stock is nearly the
            // whole item list, copyOriginalOffers was never meaningful for these. Own price is the right fix.
            var gated = index.Any(source => source.RootOffersByTemplate.ContainsKey(pending.BaseTpl));

            _unsold.Add(new UnsoldItem(pending.RelativeName, pending.BaseTpl, gated));

            if (gated)
            {
                logger.Warning(
                    $"[DRIP] {pending.RelativeName}: every offer of {pending.BaseTpl} is quest-locked, so this is " +
                    "not sold by any trader. That is deliberate - copying a quest-locked offer would make a gated " +
                    "item freely available. Leave it unsold, or gate it explicitly; do not give it its own price.");
            }
            else
            {
                logger.Warning(
                    $"[DRIP] {pending.RelativeName}: 'copyOriginalOffers' is on, but no reachable trader sells " +
                    $"{pending.BaseTpl}, so nothing sells this either. Give it its own price instead.");
            }
        }

        return created;
    }

    /// <summary>
    /// Copies an offer's child items - armour plates and soft armour inserts. Recursive, because a plate can itself
    /// have children.
    /// </summary>
    private int CopyChildren(TraderAssortIndex source, Item original, Item newParent, Trader destination)
    {
        if (!source.ChildrenByParent.TryGetValue(original.Id, out var children))
        {
            return 0;
        }

        var copied = 0;

        foreach (var child in children)
        {
            var newChild = cloner.Clone(child);
            newChild.Id = new MongoId();
            newChild.ParentId = newParent.Id;

            destination.Assort.Items.Add(newChild);
            copied++;

            copied += CopyChildren(source, child, newChild, destination);
        }

        return copied;
    }

    /// <summary>
    /// Sells the item from one trader at the config's own price.
    /// </summary>
    private bool AddOwnPricedOffer(PendingOffer pending, Trader destination)
    {
        var config = pending.Config;

        if (config.Price is null)
        {
            logger.Error(
                $"[DRIP] {pending.RelativeName}: 'price' is missing. This item has \"copyOriginalOffers\": false, " +
                "so it needs its own price. Or set \"copyOriginalOffers\": true to sell it wherever the original " +
                "is sold.");
            return false;
        }

        if (config.LoyaltyLevel is null)
        {
            logger.Error(
                $"[DRIP] {pending.RelativeName}: 'loyaltyLevel' is missing. This item has " +
                "\"copyOriginalOffers\": false, so it needs its own loyalty level.");
            return false;
        }

        var offer = new Item
        {
            Id = new MongoId(),
            Template = pending.NewItemId,
            ParentId = AssortRoot,
            SlotId = AssortRoot,
            Upd = new Upd
            {
                UnlimitedCount = true,
                StackObjectsCount = UnlimitedStackCount
            }
        };

        destination.Assort.Items.Add(offer);
        destination.Assort.LoyalLevelItems[offer.Id] = config.LoyaltyLevel.Value;
        destination.Assort.BarterScheme[offer.Id] =
        [
            [
                new BarterScheme
                {
                    Template = config.CurrencyTpl,
                    Count = config.Price.Value
                }
            ]
        ];

        AddIncludedParts(pending, destination, offer);

        return true;
    }

    /// <summary>
    /// Fills the item's own slots - armour plates, in practice. Only meaningful for own-priced items; a copied offer
    /// brings the original's plates with it.
    /// </summary>
    private void AddIncludedParts(PendingOffer pending, Trader destination, Item parent)
    {
        if (pending.Config.IncludedParts is null)
        {
            return;
        }

        foreach (var (slotName, partTpl) in pending.Config.IncludedParts)
        {
            if (!MongoId.IsValidMongoId(partTpl))
            {
                logger.Warning(
                    $"[DRIP] {pending.RelativeName}: 'includedParts' slot '{slotName}' is \"{partTpl}\", which " +
                    "isn't a 24-character item ID. Skipping it.");
                continue;
            }

            destination.Assort.Items.Add(new Item
            {
                Id = new MongoId(),
                Template = new MongoId(partTpl),
                ParentId = parent.Id,
                SlotId = slotName
            });
        }
    }
}
