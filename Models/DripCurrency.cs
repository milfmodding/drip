using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Enums;

namespace DRIP.Models;

/// <summary>
/// The currencies a Content Pack may price an item in. Deliberately narrower than the server's CurrencyType, which
/// also carries GP - a currency no DRIP content uses and that no author should be offered.
/// </summary>
public enum DripCurrency
{
    RUB,
    USD,
    EUR
}

public static class DripCurrencyExtensions
{
    /// <summary>
    /// The item template id for this currency. Taken from the server's Money enum rather than written out, so the
    /// ids cannot drift.
    /// </summary>
    public static MongoId ToTemplateId(this DripCurrency currency)
    {
        return currency switch
        {
            DripCurrency.RUB => Money.ROUBLES,
            DripCurrency.USD => Money.DOLLARS,
            DripCurrency.EUR => Money.EUROS,
            _ => Money.ROUBLES
        };
    }
}
