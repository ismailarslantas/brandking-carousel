"""Copy lint. Catches what makes a carousel dishonest, lazy or unreadable.

These are editorial rules, not reach predictions. Nothing here can say whether a
post will perform; `brandking ledger` is where real results go.
"""
from __future__ import annotations

import re

from .plan import resolve_brand, slide_text

AI_TELLS = ('delve', 'game-changer', 'game changer', 'unlock', 'unleash', 'supercharge', 'elevate your',
            'in today\'s', 'fast-paced', 'ever-evolving', 'seamless', 'revolutionize', 'revolutionise',
            'harness the power', 'navigate the', 'landscape of', 'at the end of the day', 'testament to',
            'look no further', 'dive in', 'dive into', 'it\'s not just')
HYPE = ('guaranteed', '100%', 'go viral', 'goes viral', 'overnight success', 'risk-free', 'secret formula',
        'never fail', 'instant results', 'world-class', 'industry-leading', 'best in the world')
SELF_PRAISE = ('we are proud', 'our team of experts', 'innovative solutions', 'leading provider',
               'unparalleled', 'cutting-edge', 'one-stop shop')
COMMENT_BAIT = ('comment below', 'tag a friend', 'double tap', 'like if you', 'smash the', 'link in bio for more')
GENERIC_COVERS = ('tips', 'things you should know', 'things to know', 'everything you need', 'ultimate guide',
                  'read this', 'you need to know', 'must know')
CTA_VERBS = ('save', 'send', 'share', 'try', 'read', 'book', 'join', 'get', 'start', 'download', 'visit',
             'view', 'compare', 'follow', 'apply', 'reply', 'message', 'dm', 'ask', 'see', 'use', 'build', 'keep')
#: Numbers that claim something: percentages, multipliers, money and countable outcomes.
CLAIM = re.compile(r'(\$|€|£|₺)\s?\d|\d\s?%|\b\d+(\.\d+)?\s?(x|k|m|times|people|users|customers|clients|followers|hours|days|weeks|months|years)\b', re.I)
PLACEHOLDER = re.compile(r'\b(TODO|TBD|lorem ipsum|XXX)\b|\[[^\]]+\]', re.I)


def _finding(rule, severity, detail, slide=None):
    item = {'rule': rule, 'severity': severity, 'detail': detail}
    if slide is not None:
        item['slide'] = slide
    return item


def _contains(text, phrase):
    return re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', text, re.I) is not None


def lint_plan(plan):
    """Return findings. Any fail blocks delivery; warnings are for a human to weigh."""
    out = []
    brand = resolve_brand(plan)
    voice = brand.get('voice', {})
    slides = plan['slides']
    allowed = {w.casefold() for w in voice.get('allowed_words', [])}
    banned = voice.get('banned_words', [])
    has_global_sources = bool(plan.get('sources'))
    fmt = plan.get('format', 'carousel')
    is_carousel = fmt == 'carousel'
    em_dashes = 0

    for number, slide in enumerate(slides, 1):
        text = slide_text(slide)
        em_dashes += text.count('—')
        if PLACEHOLDER.search(text):
            out.append(_finding('placeholder', 'fail', 'Unfinished placeholder text.', number))
        for phrase in banned:
            if _contains(text, phrase):
                out.append(_finding('brand_voice', 'fail', f'{phrase!r} is banned by this brand\'s voice.', number))
        for phrase in HYPE:
            if phrase not in allowed and _contains(text, phrase):
                out.append(_finding('hype_claim', 'fail', f'{phrase!r} promises what nobody can promise.', number))
        for phrase in AI_TELLS:
            if phrase not in allowed and _contains(text, phrase):
                out.append(_finding('ai_tell', 'warn', f'{phrase!r} reads as machine-written. Say the plain thing.', number))
        for phrase in SELF_PRAISE:
            if _contains(text, phrase):
                out.append(_finding('self_praise', 'warn', f'{phrase!r} talks about the brand, not the reader.', number))
        for phrase in COMMENT_BAIT:
            if _contains(text, phrase):
                out.append(_finding('comment_bait', 'warn', f'{phrase!r} is empty engagement bait.', number))
        match = CLAIM.search(text)
        if match and not (slide.get('source') or has_global_sources):
            out.append(_finding('unsourced_number', 'fail', f'{match.group(0)!r} looks like a claim. Add a source or cut it.', number))
        alt = slide.get('alt', '')
        if len(alt.split()) < 6:
            out.append(_finding('alt_text', 'warn', 'Alt text is too thin to be useful. Describe the information shown.', number))
        if re.match(r'(image|picture|photo) of\b', alt, re.I):
            out.append(_finding('alt_text', 'warn', 'Start alt text with the content, not "image of".', number))
        if slide.get('background') and re.search(r'\b(text|lettering|words?|typography|caption)\b(?! ?-?free)', slide.get('visual_prompt', ''), re.I) \
                and not re.search(r'\bno (text|lettering|words?|typography)\b', slide.get('visual_prompt', ''), re.I):
            out.append(_finding('text_in_plate', 'warn', 'Image models misspell. Ask for a text-free plate; the engine sets the type.', number))
        for sentence in re.split(r'[.!?]+', slide.get('body', '')):
            if len(sentence.split()) > 16:
                out.append(_finding('long_sentence', 'warn', 'A body sentence runs over 16 words.', number))

    if em_dashes > 1:
        out.append(_finding('em_dash', 'warn', f'{em_dashes} em dashes across the slides. Use one at most.'))

    cover = slides[0]['headline'].casefold()
    if brand.get('name', '').casefold() in cover:
        out.append(_finding('cover_about_brand', 'warn', 'The cover opens with the brand. Open with the reader.', 1))
    for phrase in GENERIC_COVERS:
        if phrase in cover:
            out.append(_finding('generic_cover', 'warn', f'{phrase!r} could sit on any account. Be specific.', 1))

    if is_carousel and len(slides) > 1:
        second = slides[1]['headline'].split()[0].casefold()
        if second in {'this', 'that', 'it', 'these', 'those', 'they', 'so', 'and', 'but'}:
            out.append(_finding('slide_two', 'warn', 'Slide two leans on the cover. Some readers meet it first, so make it stand alone.', 2))

    calls = [n for n, slide in enumerate(slides, 1) if slide.get('cta')]
    if is_carousel and len(calls) > 1:
        out.append(_finding('one_cta', 'fail', f'Slides {calls} all ask for an action. Pick one.'))
    for call in calls:
        verb = slides[call - 1]['cta'].split()[0].casefold().strip('.,!')
        if verb not in CTA_VERBS:
            out.append(_finding('cta_verb', 'warn', f'The CTA opens with {verb!r}. Open with what the reader should do.', call))
    if not calls:
        out.append(_finding('one_cta', 'warn', 'No slide asks for an action.'))

    promise = plan.get('promise')
    if not is_carousel:
        pass
    elif not promise:
        out.append(_finding('promise_payoff', 'warn', 'State what the cover promises and which slide pays it off: "promise": {"text": ..., "paid_on": n}.'))
    elif not isinstance(promise.get('paid_on'), int) or not 2 <= promise['paid_on'] <= len(slides):
        out.append(_finding('promise_payoff', 'fail', 'promise.paid_on must be a slide after the cover.'))

    captions = [(None, plan.get('caption', ''), slides[0]['headline'])] if fmt not in {'series', 'grid'} else [
        (n, slide.get('caption', ''), slide['headline']) for n, slide in enumerate(slides, 1)]
    limit = voice.get('max_hashtags', 5)
    for number, caption, headline in captions:
        if len(caption) > 2200:
            out.append(_finding('caption_length', 'fail', f'Caption is {len(caption)} characters, Instagram allows 2,200.', number))
        opening = caption.strip().split('\n')[0]
        if len(opening) > 125:
            out.append(_finding('caption_opening', 'warn', 'The first line runs past 125 characters and may be cut off in the feed.', number))
        if opening.casefold().strip(' .!') == headline.casefold().strip(' .!'):
            out.append(_finding('caption_opening', 'warn', 'The caption repeats the headline. Open from a different angle.', number))
        tags = re.findall(r'(?<!\w)#\w+', caption)
        if len(tags) > limit:
            out.append(_finding('hashtags', 'warn', f'{len(tags)} hashtags, this brand\'s limit is {limit}.', number))
        if PLACEHOLDER.search(caption):
            out.append(_finding('placeholder', 'fail', 'Caption still has placeholder text.', number))
        for phrase in HYPE:
            if phrase not in allowed and _contains(caption, phrase):
                out.append(_finding('hype_claim', 'fail', f'Caption: {phrase!r} promises what nobody can promise.', number))
        if CLAIM.search(caption) and not has_global_sources:
            source = number and slides[number - 1].get('source')
            if not source:
                out.append(_finding('unsourced_number', 'fail', 'The caption has a numeric claim but no source.', number))
    if is_carousel and not 5 <= len(slides) <= 10:
        out.append(_finding('deck_length', 'warn', f'{len(slides)} slides. Most stories fit in 5-10.'))
    return out


def score_cover(headline):
    """Rank cover options on checkable traits. An editing aid, never a reach forecast."""
    words = headline.split()
    traits = {
        'short': len(words) <= 6,
        'specific': bool(re.search(r'\d', headline)) or any(len(w.strip('.,?!')) >= 9 for w in words),
        'tension': bool(re.search(r"\b(stop|why|without|before|instead|wrong|mistake|never|not|isn't|don't|but)\b|\?", headline, re.I)),
        'addresses_reader': bool(re.search(r'\b(you|your|yours)\b', headline, re.I)),
        'no_filler': not any(phrase in headline.casefold() for phrase in GENERIC_COVERS + AI_TELLS),
    }
    return {'headline': headline, 'score': sum(traits.values()), 'traits': traits}


def has_failures(findings):
    return any(item['severity'] == 'fail' for item in findings)
