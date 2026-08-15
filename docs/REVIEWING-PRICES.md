# Reviewing prices

For Colette and Amber. No code, no JSON, no typing commands — a spreadsheet and two
double-clicks.

---

## What this is for

Every item in DRIP has a price. Some of them were set carefully. Some were copied from another
item when it was being made and never changed. Nobody can tell which is which by looking at the
mod, so this puts all of them in one spreadsheet where you can see them together and fix the
ones that look wrong.

You don't have to review all of them. The ones most likely to be wrong are sorted to the top.

---

## Doing it

**1. Double-click `Review Prices.cmd`** in the DRIP folder.

It makes a spreadsheet called **Prices to review.xlsx** and opens it.

**2. Change the prices you want to change.**

Type new numbers into the yellow **NEW PRICE** column. That's the only column to touch —
everything else is there to help you decide.

- Leave a row blank to keep its current price.
- Type the number however you like: `45000`, `45,000` and `45 000` all work.
- Don't rename or reorder anything. The tool matches rows by the **Item** column.

**3. Save the file and close Excel.**

**4. Double-click `Review Prices.cmd` again** and choose **1**.

It shows you a list of exactly what will change, and asks before doing anything. If the list
looks wrong, say no — nothing is touched until you say yes.

---

## Reading the spreadsheet

| column | what it tells you |
|---|---|
| **Item** | the internal name of the item — don't edit this, it's how rows are matched |
| **What it is** | the name players see in game |
| **Set** | the group it belongs to, like GORKA4 or GEN2. Items in a set usually cost about the same |
| **Kind** | top, bottom, or gear |
| **Sold by** | which trader sells it |
| **Level** | the player level needed to buy it |
| **Price now** | what it costs today, or **not sold yet** if nothing sells it |
| **Currency** | roubles unless it says otherwise. A few items are priced in dollars or euros |
| **Comes with** | what is already inside it — armour plates and inserts, at their in-game value |
| **NEW PRICE** | ⬅ the yellow one. Put your new number here, **in the currency on that row** |
| **Others in this set** | what the rest of the set costs — the most useful column for judging |
| **Worth a look?** | why we thought this one might be wrong |
| **Why** | the reasoning behind that |

**About the currency column.** 20 of the 171 priced items are in dollars or euros rather than
roubles, and a dollar is worth about 120 roubles in game. Every item in a set uses the same
currency, so **"Others in this set" always compares like with like** — that column is safe to
trust as it stands. The one place it matters is comparing *across* sets: an armour priced at
2,450 dollars is not cheaper than one priced at 243,844 roubles, it is slightly dearer.

## The rows that say "not sold yet"

Some items are at the top of the sheet with **not sold yet** where the price should be. Nothing
in the game sells the item they are a retexture of, so they have no shelf and nobody can buy
them. A price is what fixes that — this is the one case where the sheet is asking for a decision
rather than checking one.

Those rows need **two** things, so they have **two yellow cells**:

- **NEW PRICE** — as usual.
- **Level** — how far in with the trader someone has to be before it appears, 1 to 4. It is
  filled in with **1** already, which means available straight away. Change it if you would
  rather it were harder to get to.

**Read the "Comes with" column before you pick a number.** These are armour, and they do not
arrive empty — the plates and inserts inside them are worth far more than the carrier itself. A
TacTec shell is worth about 3,600, and the same TacTec with its armour in is worth about 180,000.
Pricing it at 3,600 would sell 180,000 of kit for the price of the bag it came in, and nothing
afterwards would look wrong.

"Others in this set" says **none priced yet** on these rows, because every other pattern in the
same set is in the same position. There is no set price to lean on — that is why "Comes with" is
there.

### "Worth a look?"

Only three things get flagged, and none of them mean the price is definitely wrong:

- **Free** — priced at 0, so players get it for nothing.
- **Odd for the set** — much higher or lower than everything else in its group.
- **Joke number** — things like 69,420 or 420,666. Several of these are probably on purpose;
  they're flagged so you can confirm rather than because they're mistakes.

Everything not flagged is left alone. A flag is a suggestion to look, nothing more.

---

## Things worth knowing

**Only items with their own price appear.** A lot of gear is sold wherever the original item is
sold, at the original's price, so there's nothing to set. Those aren't in the list — about 170
items are, not all 276.

**Nothing changes until you confirm.** The tool always shows the full before-and-after list and
waits for a yes.

**Your changes stick.** Prices are also recorded in a separate file the rebuild tools read, so
re-running anything technical later won't quietly undo your work.

**You can stop halfway.** Do ten rows, apply them, come back later. Re-exporting starts from
whatever the prices are now, so finished work shows up as already done.

---

## If something goes wrong

**"Python isn't installed"** — install it from [python.org](https://www.python.org/downloads/),
and tick *"Add Python to PATH"* during setup. Then try again.

**"No item called X"** — the Item column got edited or a row was moved. Choose option **2** to
start from a fresh spreadsheet.

**It won't read the file** — Excel may have saved it in a different format. Use *Save As* and
pick **Excel Workbook (.xlsx)**.

**Something else** — nothing will have been changed. Send the message on screen to Sophia.

---

## A few we already noticed

Not changed — these are yours to decide:

- **`COMBAT_PANTS_URBANREED_BOTTOM - Copy`** — the file is named "- Copy", the way Windows
  names a duplicate. It's the only file for that item, so it works, but the name looks
  accidental. It's also 10,000 in a set where everything else is 66,000.
- **`COMBAT_PANTS_GHOSTPARTIZAN_PANTS`** — also 10,000 in that same 66,000 set, also at level 3
  rather than 13.
- **The `USECBASE` fatigues** — four items at four different prices (30,000, 30,000, 55,000,
  65,000) where the rest of DRIP tends to price a set consistently.
