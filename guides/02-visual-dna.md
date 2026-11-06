# Visual DNA

Canvas, footer lock, typography and color. Tools and compositions live in [05-visual-tools.md](05-visual-tools.md).

**The governing idea:** the rules exist to produce **consistent variety**, not a template. Brand language stays fixed; composition, background and palette role change on every post. Two posts that look alike make a failed series.

## 1. Canvas and safe area

**Default: 1080 x 1350 (4:5 portrait).** Story: 1080 x 1920. Square (1080 x 1080) only on explicit request.

| Zone | Pixels | Rule |
| --- | --- | --- |
| Edge margin | 80 (comfortable: 96) | No text crosses this line |
| Top headline zone | 100-520 | For top-headline compositions |
| Hero zone | 380-1080 | The visual center of gravity |
| Lower card zone | 760-1150 | For frosted card and panel compositions |
| Footer strip | 1180-1300 | Logo and contact |
| Micro text | 24-28 px | Web, phone, @handle |

**Story (1080 x 1920):** Instagram's interface covers the top 250 px and bottom 320 px. Headline 400-900, CTA 1250-1500, footer 1500-1650. Do not enlarge a post, rebuild it. Stories carry less: a headline, one line and a CTA.

## 2. Footer locks

Choose by brand type and keep it **exactly the same across the series**. The footer is the strongest thing holding a series together. If its position or size shifts between posts, the grid falls apart.

| Lock | Layout | Good for |
| --- | --- | --- |
| **A: Centered** | Logo bottom center at 1180-1300, nothing beside it | Product brands: food, cosmetics, agriculture, retail |
| **B: Split** | Logo bottom left, web or phone bottom right, same baseline at 1230-1290 | Service brands: consulting, construction, property, B2B |
| **C: Dual brand** | Two logos with a thin vertical divider at bottom left, web at bottom right | Project brands, co-productions, dealerships |
| **D: Series strip** | Three-part strip: logo left, action or app badges center, phone or location right. Identical on every post | Direct sales, charities, app-based services, franchises |
| **E: Top symbol plus strip** | The brand's plain symbol at top center, 60-80 px. A thin strip below with a Follow pill, generic social icons and web address | Template series, property portfolios, multi-post calendars |

Badge examples for D: an order-line pill, app store badges, a chat icon, a location pin, a campaign badge. In E, the symbol seals the canvas from the top and the strip closes it, which frames the grid.

**Legal micro text (optional):** telecom, finance and campaign posts can carry 18-20 px terms below the footer. It is not expected to be read at phone size; it signals seriousness. If terms must be understood, put them in the caption too.

The engine renders locks A and B through `footer: center` and `footer: split`. Locks C, D and E are available in full-design images.

## 3. Typography: three branches

Choose a branch by brand category. Branches do not mix.

### Branch 1: Sans (energy, accessibility, trust)

Geometric or humanist sans: Poppins, Montserrat, Gilroy, Museo Sans, Figtree. *Agriculture, food, children, health, technology, education, retail, construction, services, charities.*

### Branch 2: Serif (prestige, quiet luxury, maturity)

Modern serif with fine contrast: Playfair Display, Cormorant, Freight Display, Canela, Fraunces. *Luxury housing, jewelry, hospitality, art, boutique services.* Headlines are serif; supporting text and CTA stay sans.

### Branch 3: Hybrid (script plus condensed capitals)

Two fonts collide: a slanted handwritten script and tight condensed capitals. The script carries context and feeling, the capitals carry the claim. Script: Brittany, Sacramento, Bakerie. Capitals: Anton, Bebas Neue, Oswald, Druk. *Fast food, cafes, retro, sports, youth, events, festivals.*

- The script line is **always short**, 1-3 words. Long script cannot be read.
- Script and capitals sit **one above the other**, never on the same line.
- If one is tilted, the other stays straight.
- Capital lines use line spacing of **0.85-0.92**, so letters lean on each other.
- An underline, strip or rough brush stroke can carry emphasis.
- Supporting text and CTA stay sans.

### Shared scale

| Layer | Size | Weight |
| --- | --- | --- |
| Eyebrow | 34-44 px | Light or Regular |
| Headline line 1 | 76-96 px | Light or Regular |
| Headline line 2 | 88-130 px | Bold or ExtraBold, **emphasis lands here** |
| Giant type | 160-320 px | Black or ExtraBold, capitals |
| Supporting text | 42-56 px | Regular, with bold emphasis inside |
| Card or list text | 30-46 px | Medium |
| CTA | 36-46 px | SemiBold |
| Numeric highlight | 90-160 px | Black |
| Micro footer | 22-28 px | Regular |

### Type rules

- **Two weights:** one light line and one bold line. Contrast comes from here.
- Headline line spacing is **0.92-1.00**. A tightly stacked block is part of the signature.
- Tracking is slightly negative on bold headlines and neutral on a light eyebrow.
- **Wide-tracked eyebrow:** the eyebrow can run in capitals at +0.20em for corporate seriousness.
- **One emphasis.** A single word or phrase changes color or weight.
- **All caps** belongs in giant type, diagonal type and repeat walls. Normal headlines use sentence case.
- **Diagonal placement** only works with giant capitals. Thin or small text never tilts.
- **Punctuation sets the tone:** an exclamation mark sells, a period is quiet luxury, a colon sets up a payoff, a question mark invites interaction.

The engine maps these branches to its houses: `sovereign` (sans), `editorial` (serif) and `poster` (condensed capitals).

## 4. Color and palette rotation

### Structure

One **dominant field**, one **accent** and a **text color**, roughly 70/20/10. Neutrals such as white, cream, charcoal and gray do not count as colors.

### Palette rotation: the heart of the system

A brand has two or three colors, yet nine posts need not look alike, because **colors change roles on each post**.

| Rotation | Field | Accent | Effect |
| --- | --- | --- | --- |
| **R1: Solid** | Brand color, flat | White or cream text | Corporate, assertive |
| **R2: Photo-led** | Scene photo | Brand-colored card or strip | Warm, real |
| **R3: Light mode** | White, pale gray or cream | Brand-colored text and pill | Airy, premium |
| **R4: Dark mode** | Dark neutral: charcoal, night, deep green | Brand color at one point | Luxurious, mysterious |
| **R5: Duotone** | Photo tinted to the brand color | White text or prop | Graphic, striking |
| **R6: Secondary** | Complementary color: sky, cream, turquoise | Brand color accent | Lets the series breathe |
| **R7: Gradient** | Brand color, dark to light | White plus translucent cards | Digital, modern |
| **R8: Pattern** | Tone-on-tone pattern: contours, waves, dots, giant letters | Brand-colored text | Rich yet calm |
| **R9: Warm neutral** | Cream, beige or sand, such as `#F2E6D0` | Brand-colored text and product | Nostalgic, appetizing |

**Rule:** use at least **four rotations** in a series. The same rotation never appears twice in a row and never sits side by side or stacked in the grid.

*Example, a purple education software palette:* purple gradient with a cutout group (R7), pale gray with purple bento cards (R3), purple gradient with a device mockup (R7, another composition), green chalkboard texture with an orange blob (R6), deep purple with floating cards (R4). Five posts, one palette, five looks.

The engine's `solid`, `light`, `dark` and `warm` roles correspond to R1, R3, R4 and R9, and the `photo` layout covers R2. The other rotations are available in full-design images.

### Tone-on-tone pattern (R8)

When a flat field feels dull, add **texture** rather than color. The pattern shares the field's color at 8-15% brightness difference and never disturbs the text.

Types: topographic contours, radial waves, dot grid, giant repeated letters or words, checkerboard (fast food, retro), fine crosshatch, scattered leaves or organic shapes.

**Rule:** one pattern, one direction. Two patterns never overlap.

### Gradients

For depth in digital and modern categories:

- Two tones from one family, such as purple to lilac. Never three colors.
- Direction: diagonal, dark top left to light bottom right, or radial with a light center.
- Text on a gradient is always white. Cards are translucent white or solid brand color.

### Reference palettes

| Category | Dominant | Accent | Text |
| --- | --- | --- | --- |
| Agriculture, biotech | Deep petrol green `#0E3B32` | Lime `#C6F542` | White |
| Children, health | Blue to purple `#0A7BE0 → #7B2FD4` | White plus mint `#BFEBD9` | White |
| Food, desserts | Burgundy red `#A81419` | Cream gold `#EBD79A` | Cream |
| Food, daily goods | Red `#E01B24` | Yellow `#FFC72C` | White |
| Consulting, property | Burgundy `#8E1230` | Red `#D0021B` | White |
| Luxury housing | Red `#C8102E` | Cream `#F2EFE9` | Charcoal or white |
| Construction | Blue `#1B54D6` | Gold cream `#E8D5A8` | White |
| Education, software | Purple gradient `#4B1BA8 → #A855F7` | White plus lilac `#E9D5FF` | White |
| Data, consulting | Cobalt `#1B44D6` | White plus pale gray `#EEF1F6` | White or navy |
| Charity, donations | Red `#D6112B` | White plus sky `#7EC8E3` | White |
| Cold desserts, fresh | Turquoise `#1FB6A8` | Cream plus pink `#F2A8C4` | White |
| Fast food, chicken, burgers | Red `#D81F26` | Yellow `#FFC629` | White or cream |
| Fast food, warm neutral | Cream beige `#F2E6D0` | Red `#E8352A` | Dark brown |
| Property, energetic | Orange `#F4631E` | White plus charcoal | White |
| Property, nature | Green gradient `#2E7D32 → #8BC34A` | White | White |
| Property, corporate | Navy `#152C5B` | Yellow `#FFD200` | White |
| Telecom, services | Blue `#0B63CE` | Light blue `#5AB8FF` | White |

For a new brand, make the logo's main color dominant, choose a bright accent from its complement, and do not add a third color. A brand's own confirmed palette always overrides these starting points.

## 5. Photography

- **Light:** golden hour, blue hour or soft studio. No harsh midday sun.
- **Framing:** a slightly low angle makes the subject heroic.
- **Depth:** soft background bokeh. Keep the area where text will land deliberately plain.
- **People:** real, local people who do not pose like actors. Calm posture for corporate work at 40+; natural smiles and cutouts for education and youth brands. Use only authorized portraits.
- **Cutouts:** a person with the background removed, placed on the field with a soft shadow beneath. Edges must be clean. If hair has a halo, do not use it.
- **Texture:** real surfaces such as soil, wood, marble, paper, leaves, concrete and chalk.
- **Product:** always sharp, with a shadow that grounds it. If floating, support it with shadow and glow.

## 6. Common mistakes

| Mistake | Instead |
| --- | --- |
| Adding shadow or outline to make a headline readable | Put a frosted card or highlight bar behind it |
| Two accent colors | One accent, one place |
| Shifting the footer between posts | Pixel-identical |
| Darkening a photo to write over it | Use a card and leave the photo alone |
| Repeating one rotation for nine posts | At least four rotations |
| Text 30 px from the edge | 80 px margin |
| Eight bullets on one post | Move the extras into a carousel |
| Serif and sans headlines in one post | Pick a branch and stay in it |
| Tilting thin text | Diagonal is for giant capitals only |
| Three-color gradients | Two tones, one color family |
| Script in a long sentence | Three words at most |
| Script and capitals on one line | Stack them |
| Two overlapping patterns | One pattern, one direction |
| A shaped mask that cuts the product | The mask holds the product entirely |
