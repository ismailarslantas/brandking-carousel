import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from PIL import Image

from brandking import audit, brandkit, cli, deliver, gate, images, ledger, lint, memory, runs
from brandking.canvas import Canvas
from brandking.core import PlanError, ROOT, asset_path, contrast, project_dir, read_json
from brandking.layouts import LAYOUT_FUNCTIONS, render_slide, thread_y
from brandking.plan import LAYOUTS, resolve_brand, validate

# Tests must never touch the user's real brand memory.
_MEMORY = tempfile.TemporaryDirectory(prefix='brandking-test-memory-')
os.environ['BRANDKING_HOME'] = _MEMORY.name

DEMO = ROOT / 'examples/demo.json'
FIGTREE = ROOT / 'assets/fonts/Figtree.ttf'


class Workspace(unittest.TestCase):
    def setUp(self):
        self.plan = read_json(DEMO)
        (ROOT / 'outputs').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='carousel test ', dir=ROOT / 'outputs')
        self.dir = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def write_plan(self, plan=None, name='plan.json'):
        path = self.dir / name
        path.write_text(json.dumps(plan or self.plan), encoding='utf-8')
        return path

    def slide(self, **fields):
        base = {'layout': 'statement', 'rotation': 'light', 'headline': 'A plain headline', 'alt': 'x', 'visual_prompt': 'x'}
        return {**base, **fields}


class Delivery(Workspace):
    def test_full_delivery(self):
        out = self.dir / 'delivery'
        result = deliver.render(DEMO, out)
        self.assertEqual(result['status'], 'passed')
        slides = list((out / 'slides').glob('*.png'))
        self.assertEqual(len(slides), 6)
        for path in slides:
            with Image.open(path) as image:
                self.assertEqual(image.size, (1080, 1350))
        for name in ('contact-sheet.jpg', 'slides.pdf', 'previews/swipe-strip.jpg', 'previews/grid-tile.jpg',
                     'visual-prompts.md', 'upload-checklist.md', 'caption.txt', 'alt-texts.md', 'manifest.json'):
            self.assertTrue((out / name).is_file(), name)
        with zipfile.ZipFile(out / 'carousel.zip') as archive:
            names = archive.namelist()
        self.assertIn('slides/01.png', names)
        self.assertIn('editable/recipe/brandking/cli.py', names)
        self.assertIn('editable/recipe/assets/fonts/Figtree.ttf', names)
        report = read_json(out / 'qa-report.json')
        self.assertEqual(report['automatic'], 'passed')
        self.assertEqual(report['visual'], 'pending')

    def test_output_must_be_empty(self):
        out = self.dir / 'delivery'
        deliver.render(DEMO, out)
        with self.assertRaises(PlanError):
            deliver.render(DEMO, out)

    def test_every_example_passes(self):
        for path in sorted((ROOT / 'examples').glob('*.json')):
            with self.subTest(path.name):
                self.assertTrue(deliver.check(read_json(path))['ok'])

    def test_portable_recipe_renders_on_its_own(self):
        out = self.dir / 'delivery'
        deliver.render(DEMO, out)
        recipe = read_json(out / 'editable/recipe/plan.json')
        self.assertIsInstance(recipe['brand'], dict)
        self.assertTrue((out / 'editable/recipe/assets/brand/logo-horizontal.png').is_file())

    def test_same_plan_gives_the_same_pixels(self):
        first = deliver.build(self.plan)[1][0].im.tobytes()
        second = deliver.build(self.plan)[1][0].im.tobytes()
        self.assertEqual(first, second)

    def test_failed_audit_withholds_the_archive(self):
        self.plan['slides'][1]['body'] = 'Guaranteed results for everyone.'
        out = self.dir / 'delivery'
        result = deliver.render(self.write_plan(), out)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse((out / 'carousel.zip').exists())
        self.assertEqual(read_json(out / 'qa-report.json')['automatic'], 'failed')

    def test_covers_ranks_options_and_keeps_the_disclaimer(self):
        out = self.dir / 'covers'
        ranking = deliver.covers(DEMO, out)
        self.assertEqual(len(ranking), 3)
        self.assertTrue((out / 'cover-sheet.jpg').is_file())
        self.assertIn('does not predict', read_json(out / 'cover-ranking.json')['note'])

    def test_covers_needs_three_options(self):
        self.plan['cover_options'] = ['One', 'Two']
        with self.assertRaises(PlanError):
            deliver.covers(self.write_plan(), self.dir / 'covers')

    def test_prompt_pack_keeps_plates_text_free(self):
        pack = images.prompts_markdown(self.plan)
        self.assertIn('no text, no lettering', pack)
        self.assertIn(resolve_brand(self.plan)['accent'], pack)


class Validation(Workspace):
    def test_long_headline_rejected(self):
        self.plan['slides'][0]['headline'] = 'This headline has far too many words for reading'
        with self.assertRaises(PlanError):
            validate(self.plan)

    def test_repeated_layout_rejected(self):
        self.plan['slides'][1]['layout'] = 'cover'
        with self.assertRaises(PlanError):
            validate(self.plan)

    def test_repeat_allowed_for_declared_product_variants(self):
        self.plan['product_variant_exception'] = True
        for slide in self.plan['slides'][1:]:
            slide['rotation'] = self.plan['slides'][0]['rotation']
        validate(self.plan)

    def test_path_traversal_rejected(self):
        with self.assertRaises(PlanError):
            asset_path('../outside.png')

    def test_brand_kit_outside_project_rejected(self):
        with self.assertRaises(PlanError):
            resolve_brand({'brand': '../elsewhere'})

    def test_missing_image_rejected(self):
        self.plan['slides'][1]['image'] = 'missing.png'
        self.plan['slides'][1].pop('body')
        with self.assertRaises(PlanError):
            validate(self.plan)

    def test_focus_must_be_a_fraction(self):
        self.plan['slides'][1]['focus_y'] = 4
        with self.assertRaises(PlanError):
            validate(self.plan)

    def test_stat_needs_a_source(self):
        self.plan['slides'][1] = self.slide(layout='stat', value='42%')
        with self.assertRaises(PlanError):
            validate(self.plan)

    def test_quote_needs_attribution(self):
        self.plan['slides'][1] = self.slide(layout='quote', source='x')
        with self.assertRaises(PlanError):
            validate(self.plan)

    def test_missing_glyph_rejected(self):
        self.plan['slides'][1]['headline'] = 'Crown \U0001F451 here'
        with self.assertRaises(PlanError):
            validate(self.plan)

    def test_emphasis_must_come_from_headline(self):
        self.plan['slides'][0]['emphasis'] = 'nonsense'
        with self.assertRaises(PlanError):
            validate(self.plan)

    def test_too_many_slides_rejected(self):
        self.plan['slides'] = self.plan['slides'] * 4
        with self.assertRaises(PlanError):
            validate(self.plan)

    def test_turkish_glyphs_survive(self):
        self.plan['slides'][1]['headline'] = 'Şöyle güçlü bir başlık'
        validate(self.plan)


class Rendering(Workspace):
    def render(self, spec, brand=None):
        brand, body, title = validate(self.plan) if brand is None else (brand, FIGTREE, FIGTREE)
        return render_slide(spec, brand, 2, 6, (body, title))

    def test_every_layout_is_registered_and_documented(self):
        self.assertEqual(set(LAYOUTS), set(LAYOUT_FUNCTIONS))

    def test_each_layout_renders_cleanly_in_each_palette_role(self):
        specs = {
            'cover': {'headline': 'A short cover'},
            'statement': {'body': 'One plain sentence for the reader.'},
            'split': {'items': ['First panel', 'Second panel']},
            'steps': {'items': ['One', 'Two', 'Three']},
            'checklist': {'items': ['One', 'Two', 'Three']},
            'timeline': {'items': ['One', 'Two', 'Three', 'Four']},
            'versus': {'left_label': 'Before', 'right_label': 'After', 'items': ['Slow | Fast', 'Vague | Clear']},
            'myth': {'myth': 'Longer is always better', 'fact': 'Clearer is better'},
            'stat': {'value': '4:5', 'source': 'Engine specification'},
            'quote': {'attribution': 'A real person', 'source': 'A real interview'},
            'bento': {'items': ['One', 'Two', 'Three', 'Four']},
            'closing': {'body': 'One plain line.', 'cta': 'Save this'},
        }
        for layout, fields in specs.items():
            for rotation in ('solid', 'light', 'dark', 'warm'):
                with self.subTest(layout=layout, rotation=rotation):
                    canvas = self.render(self.slide(layout=layout, rotation=rotation, **fields))
                    findings = audit.audit_contrast(canvas, 1) + audit.audit_layout(canvas, 1, False)
                    self.assertEqual([f for f in findings if f['severity'] == 'fail'], [])

    def test_overflow_rejected_not_shrunk(self):
        canvas = Canvas('#FFFFFF', FIGTREE, FIGTREE)
        with self.assertRaises(PlanError):
            canvas.text('Too much text in a tiny area', (96, 100, 200, 110), 48, '#111111')

    def test_slide_number_in_layout_errors(self):
        spec = self.slide(layout='steps', items=['This long row cannot possibly fit on one single line of the numbered step layout at all'])
        with self.assertRaisesRegex(PlanError, 'Slide 2'):
            self.render(spec)

    def test_svg_escapes_text(self):
        canvas = Canvas('#FFFFFF', FIGTREE, FIGTREE)
        canvas.text('İ ı Ç ç Ğ ğ Ö ö Ş ş Ü ü < & >', (96, 100, 984, 400), 36, '#111111')
        canvas.finish()
        self.assertIn('&lt;', ''.join(canvas.svg))
        self.assertIn('&amp;', ''.join(canvas.svg))

    def test_second_brand_changes_output(self):
        brand, body, title = validate(self.plan)
        spec = self.plan['slides'][0]
        first = render_slide(spec, brand, 1, 6, (body, title))
        other = {**copy.deepcopy(brand), 'primary': '#3B1835', 'accent': '#FFDCA8', 'name': 'SECOND BRAND'}
        second = render_slide(spec, other, 1, 6, (body, title))
        self.assertNotEqual(first.im.tobytes(), second.im.tobytes())

    def test_product_photo_keeps_its_aspect_ratio(self):
        photo = self.dir / 'product.png'
        Image.new('RGBA', (200, 100), '#FF0000').save(photo)
        canvas = Canvas('#FFFFFF', FIGTREE, FIGTREE)
        canvas.image(photo, (100, 400, 500, 800))
        canvas.finish()
        self.assertEqual(canvas.im.getpixel((200, 450)), (255, 255, 255))
        self.assertEqual(canvas.im.getpixel((200, 550)), (255, 0, 0))

    def test_thread_wave_meets_itself_at_every_seam(self):
        self.assertAlmostEqual(thread_y(0), thread_y(1080))

    def test_text_alignment(self):
        canvas = Canvas('#FFFFFF', FIGTREE, FIGTREE)
        canvas.text('Right', (100, 100, 900, 200), 40, '#111111', align='right')
        canvas.finish()
        self.assertAlmostEqual(canvas.ops[0]['bounds'][2], 900, delta=4)


class PixelAudit(Workspace):
    def photo_plate(self, color):
        path = self.dir / f'{color[1:]}.png'
        Image.new('RGB', (1080, 1350), color).save(path)
        return path.relative_to(ROOT).as_posix()

    def build_photo(self, color, rotation='dark'):
        brand, body, title = validate(self.plan)
        spec = self.slide(layout='photo', rotation=rotation, panel=False, background=self.photo_plate(color))
        return render_slide(spec, brand, 2, 6, (body, title))

    def test_contrast_is_measured_on_real_pixels(self):
        # Dark role means ivory ink. The plan looks fine; the picture is what breaks it.
        findings = audit.audit_contrast(self.build_photo('#F6F7F2'), 2)
        self.assertTrue(any(f['severity'] == 'fail' for f in findings))

    def test_same_type_passes_on_a_dark_picture(self):
        findings = audit.audit_contrast(self.build_photo('#101010'), 2)
        self.assertFalse(any(f['severity'] == 'fail' for f in findings))

    def test_bright_patch_behind_a_few_letters_is_caught(self):
        path = self.dir / 'patch.png'
        image = Image.new('RGB', (1080, 1350), '#101010')
        # The plate is cropped to fit the slide, so this lands behind the first words.
        image.paste('#F6F7F2', (96, 310, 330, 440))
        image.save(path)
        brand, body, title = validate(self.plan)
        spec = self.slide(layout='photo', rotation='dark', panel=False, background=path.relative_to(ROOT).as_posix())
        canvas = render_slide(spec, brand, 2, 6, (body, title))
        self.assertTrue(any(f['severity'] == 'fail' for f in audit.audit_contrast(canvas, 2)))

    def test_photo_panel_hugs_its_copy_and_stays_readable(self):
        brand, body, title = validate(self.plan)
        plate = self.photo_plate('#F6F7F2')
        short = render_slide(self.slide(layout='photo', rotation='dark', background=plate), brand, 2, 6, (body, title))
        tall = render_slide(self.slide(layout='photo', rotation='dark', background=plate, body='One longer sentence that takes up more room in the panel than a headline.'), brand, 2, 6, (body, title))
        top = lambda canvas: min(op['bounds'][1] for op in canvas.ops if op['role'] == 'headline')
        self.assertLess(top(tall), top(short))
        for canvas in (short, tall):
            self.assertFalse(any(f['severity'] == 'fail' for f in audit.audit_contrast(canvas, 2)))

    def test_small_text_fails_phone_floor(self):
        canvas = Canvas('#FFFFFF', FIGTREE, FIGTREE)
        canvas.text('Tiny text', (100, 200, 900, 300), 18, '#111111')
        canvas.finish()
        self.assertTrue(any(f['check'] == 'phone_legibility' for f in audit.audit_layout(canvas, 1, False)))

    def test_text_outside_safe_area_fails(self):
        canvas = Canvas('#FFFFFF', FIGTREE, FIGTREE)
        canvas.text('Edge', (10, 200, 900, 300), 40, '#111111')
        canvas.finish()
        self.assertTrue(any(f['check'] == 'safe_area' for f in audit.audit_layout(canvas, 1, False)))

    def test_overlapping_blocks_fail(self):
        canvas = Canvas('#FFFFFF', FIGTREE, FIGTREE)
        canvas.text('First block', (100, 200, 900, 300), 40, '#111111')
        canvas.text('Second block', (120, 205, 900, 300), 40, '#111111')
        canvas.finish()
        self.assertTrue(any(f['check'] == 'text_collision' for f in audit.audit_layout(canvas, 1, False)))

    def test_seams_measured_and_reported(self):
        brand, canvases = deliver.build(self.plan)
        findings = audit.audit_thread(canvases, True)
        self.assertEqual(findings[0]['severity'], 'pass')

    def test_broken_seam_detected(self):
        brand, canvases = deliver.build(self.plan)
        canvases[1].im.paste(canvases[1].bg, (0, 1130, 40, 1180))
        self.assertTrue(any(f['severity'] == 'fail' for f in audit.audit_thread(canvases, True)))

    def test_thread_off_is_skipped_not_passed(self):
        finding = audit.audit_thread([], False)[0]
        self.assertEqual(finding['severity'], 'skipped')
        self.assertTrue(finding['detail'])

    def test_variant_exception_skips_rhythm_with_reason(self):
        finding = audit.audit_rhythm([], True)[0]
        self.assertEqual(finding['severity'], 'skipped')

    def test_identical_neighbours_warn(self):
        brand, canvases = deliver.build(self.plan)
        findings = audit.audit_rhythm([canvases[0], canvases[0]], False)
        self.assertEqual(findings[0]['severity'], 'warn')

    def test_grid_crop_applies_to_the_cover(self):
        canvas = Canvas('#FFFFFF', FIGTREE, FIGTREE)
        canvas.text('Edge', (10, 200, 900, 300), 40, '#111111')
        canvas.finish()
        self.assertTrue(any(f['check'] == 'grid_crop' for f in audit.audit_layout(canvas, 1, True)))


class CopyLint(Workspace):
    def rules(self, severity=None):
        return {f['rule'] for f in lint.lint_plan(self.plan) if severity in (None, f['severity'])}

    def test_demo_has_no_failures(self):
        self.assertEqual(self.rules('fail'), set())

    def test_unsourced_number_blocks(self):
        self.plan['slides'][1]['body'] = 'This tripled reach by 300% in weeks.'
        self.assertIn('unsourced_number', self.rules('fail'))

    def test_source_clears_the_number(self):
        self.plan['slides'][1]['body'] = 'This tripled reach by 300% in weeks.'
        self.plan['slides'][1]['source'] = 'Internal report, March'
        self.assertNotIn('unsourced_number', self.rules('fail'))

    def test_counting_words_are_not_claims(self):
        self.plan['slides'][1]['body'] = 'Use 3 slides for this idea.'
        self.assertNotIn('unsourced_number', self.rules())

    def test_hype_blocks(self):
        self.plan['slides'][1]['body'] = 'Guaranteed to go viral.'
        self.assertIn('hype_claim', self.rules('fail'))

    def test_placeholder_blocks(self):
        self.plan['slides'][1]['body'] = 'TODO write this.'
        self.assertIn('placeholder', self.rules('fail'))

    def test_brand_voice_banned_word_blocks(self):
        self.plan['slides'][1]['body'] = 'A growth hack for readers.'
        self.assertIn('brand_voice', self.rules('fail'))

    def test_ai_tell_warns(self):
        self.plan['slides'][1]['body'] = 'Let us delve into hooks.'
        self.assertIn('ai_tell', self.rules('warn'))

    def test_two_calls_to_action_block(self):
        self.plan['slides'][1]['cta'] = 'Save this'
        self.assertIn('one_cta', self.rules('fail'))

    def test_comment_bait_warns(self):
        self.plan['slides'][5]['cta'] = 'Tag a friend'
        self.assertIn('comment_bait', self.rules('warn'))

    def test_slide_two_must_stand_alone(self):
        self.plan['slides'][1]['headline'] = 'This changes everything.'
        self.assertIn('slide_two', self.rules('warn'))

    def test_invalid_payoff_blocks(self):
        self.plan['promise']['paid_on'] = 99
        self.assertIn('promise_payoff', self.rules('fail'))

    def test_long_caption_blocks(self):
        self.plan['caption'] = 'x' * 2201
        self.assertIn('caption_length', self.rules('fail'))

    def test_caption_numeric_claim_blocks(self):
        self.plan['caption'] += '\nThis doubled sales by 50%.'
        self.assertIn('unsourced_number', self.rules('fail'))

    def test_too_many_hashtags_warn(self):
        self.plan['caption'] += ' #a #b #c #d #e #f'
        self.assertIn('hashtags', self.rules('warn'))

    def test_thin_alt_text_warns(self):
        self.plan['slides'][1]['alt'] = 'A slide'
        self.assertIn('alt_text', self.rules('warn'))

    def test_generic_cover_warns(self):
        self.plan['slides'][0]['headline'] = '5 tips for your brand'
        self.assertIn('generic_cover', self.rules('warn'))

    def test_score_cover_is_a_trait_checklist(self):
        strong = lint.score_cover('Why your carousel loses readers?')
        weak = lint.score_cover('Everything you need to know about tips and more things')
        self.assertGreater(strong['score'], weak['score'])


class BrandKits(Workspace):
    def test_init_and_check(self):
        folder = brandkit.init_kit('acme', 'Acme', '#123456', '#FFAA00', root=self.dir)
        result = brandkit.check_kit(folder)
        self.assertEqual([f for f in result['findings'] if f['severity'] == 'fail'], [])

    def test_derived_palette_has_readable_ink(self):
        palette = brandkit.derive_palette('#7A1F3D', '#F2C14E')
        for role in ('primary', 'light', 'warm', 'dark'):
            best = max(contrast(palette['dark'], palette[role]), contrast(palette['light'], palette[role]))
            self.assertGreaterEqual(best, 4.5, role)

    def test_existing_kit_is_not_overwritten(self):
        brandkit.init_kit('acme', 'Acme', '#123456', '#FFAA00', root=self.dir)
        with self.assertRaises(PlanError):
            brandkit.init_kit('acme', 'Other', '#123456', '#FFAA00', root=self.dir)

    def test_bad_slug_rejected(self):
        with self.assertRaises(PlanError):
            brandkit.init_kit('../evil', 'x', '#123456', '#FFAA00', root=self.dir)

    def test_plan_can_point_at_a_kit(self):
        self.assertEqual(resolve_brand(self.plan)['name'], 'BRANDKING')


class Ledger(Workspace):
    def test_groups_are_flagged_until_there_are_enough_posts(self):
        file = self.dir / 'ledger.jsonl'
        for n in range(5):
            ledger.add({'id': f'a{n}', 'hook_type': 'contrast', 'reach': 1000, 'saves': 20, 'sends': 10}, file)
        ledger.add({'id': 'b', 'hook_type': 'question', 'reach': 1000, 'saves': 90, 'sends': 50}, file)
        rows = {r['value']: r for r in ledger.report(file)['groups']['hook_type']}
        self.assertEqual(rows['contrast']['saves_per_1k'], 20.0)
        self.assertEqual(rows['contrast']['confidence'], 'pattern worth testing')
        self.assertIn('too few', rows['question']['confidence'])

    def test_reach_is_required(self):
        with self.assertRaises(PlanError):
            ledger.add({'id': 'x', 'saves': 3}, self.dir / 'l.jsonl')

    def test_negative_metric_rejected(self):
        with self.assertRaises(PlanError):
            ledger.add({'id': 'x', 'reach': 10, 'saves': -1}, self.dir / 'l.jsonl')

    def test_empty_ledger_reports_nothing(self):
        self.assertEqual(ledger.report(self.dir / 'none.jsonl')['posts'], 0)


class Gates(Workspace):
    def test_signoff_moves_visual_out_of_pending(self):
        out = self.dir / 'delivery'
        deliver.render(DEMO, out)
        runs.signoff(out, 'critic', '1-6', 'Inspected at phone size.')
        self.assertEqual(read_json(out / 'qa-report.json')['visual'], 'approved')

    def test_signoff_needs_notes(self):
        out = self.dir / 'delivery'
        deliver.render(DEMO, out)
        with self.assertRaises(PlanError):
            runs.signoff(out, 'critic', '1-6', '')

    def test_failed_delivery_cannot_be_signed_off(self):
        self.plan['slides'][1]['body'] = 'Guaranteed results for everyone.'
        out = self.dir / 'delivery'
        deliver.render(self.write_plan(), out)
        with self.assertRaises(PlanError):
            runs.signoff(out, 'critic', '1-6', 'Looks fine.')

    def test_run_status_comes_from_evidence(self):
        run_id = f'test-{self.dir.name.replace(" ", "-")}'
        folder = runs.new_run(run_id)
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        status = runs.status(run_id)
        done = {g['gate']: g['done'] for g in status['gates']}
        self.assertTrue(done['brief'])
        self.assertFalse(done['automatic_qa'])
        self.assertIn('Scout', status['next'])

    def test_run_id_cannot_escape(self):
        with self.assertRaises(PlanError):
            runs.new_run('../../evil')


class Formats(Workspace):
    def grid(self):
        return read_json(ROOT / 'examples/grid.json')

    def test_single_post_has_no_counter_or_thread(self):
        plan = read_json(ROOT / 'examples/post.json')
        brand, canvases = deliver.build(plan)
        self.assertEqual(len(canvases), 1)
        self.assertIsNone(canvases[0].thread_color)
        self.assertFalse(any(op['role'] == 'counter' for op in canvases[0].ops))
        result = deliver.check(plan)
        self.assertEqual(next(f for f in result['audit'] if f['check'] == 'thread_seams')['severity'], 'skipped')

    def test_post_with_two_slides_rejected(self):
        plan = read_json(ROOT / 'examples/post.json')
        plan['slides'] = plan['slides'] * 2
        with self.assertRaises(PlanError):
            validate(plan)

    def test_grid_needs_nine(self):
        plan = self.grid()
        plan['slides'] = plan['slides'][:8]
        with self.assertRaises(PlanError):
            validate(plan)

    def test_grid_rejects_a_matching_vertical_neighbour(self):
        plan = self.grid()
        plan['slides'][3]['rotation'] = plan['slides'][0]['rotation']
        with self.assertRaisesRegex(PlanError, 'touch'):
            validate(plan)

    def test_grid_rejects_a_matching_horizontal_neighbour(self):
        plan = self.grid()
        plan['slides'][1]['rotation'] = plan['slides'][0]['rotation']
        with self.assertRaisesRegex(PlanError, 'touch'):
            validate(plan)

    def test_grid_row_ends_are_not_neighbours(self):
        plan = self.grid()
        roles = ['solid', 'light', 'dark', 'dark', 'solid', 'light', 'warm', 'dark', 'solid']
        for slide, role in zip(plan['slides'], roles):
            slide['rotation'] = role
        validate(plan)

    def test_grid_limits_a_layout_to_two(self):
        plan = self.grid()
        for n in (0, 4, 8):
            plan['slides'][n]['layout'] = 'statement'
            plan['slides'][n]['body'] = 'One plain line.'
        with self.assertRaisesRegex(PlanError, 'more than twice'):
            validate(plan)

    def test_grid_needs_a_caption_per_post(self):
        plan = self.grid()
        del plan['slides'][4]['caption']
        with self.assertRaisesRegex(PlanError, 'own caption'):
            validate(plan)

    def test_grid_delivery_has_map_and_reverse_upload(self):
        out = self.dir / 'grid'
        result = deliver.render(ROOT / 'examples/grid.json', out)
        self.assertEqual(result['status'], 'passed')
        self.assertTrue((out / 'previews/grid-map.jpg').is_file())
        self.assertFalse((out / 'previews/swipe-strip.jpg').exists())
        self.assertIn('reverse order', (out / 'upload-checklist.md').read_text(encoding='utf-8'))
        self.assertIn('Post 9', (out / 'caption.txt').read_text(encoding='utf-8'))

    def test_series_allows_a_call_to_action_per_post(self):
        plan = self.grid()
        plan['format'] = 'series'
        plan['slides'] = plan['slides'][:5]
        for slide in plan['slides'][:2]:
            slide['cta'] = 'Visit us today'
        rules = {f['rule'] for f in lint.lint_plan(plan) if f['severity'] == 'fail'}
        self.assertNotIn('one_cta', rules)

    def test_unknown_format_rejected(self):
        self.plan['format'] = 'reel'
        with self.assertRaises(PlanError):
            validate(self.plan)


class ImageBridge(Workspace):
    def picture(self, size, name='raw.png'):
        path = self.dir / name
        Image.new('RGB', size, '#336699').save(path)
        return path

    def test_fit_reaches_the_exact_size(self):
        for fmt, source in (('post', (1024, 1280)), ('story', (1024, 1820)), ('square', (1024, 1024))):
            out = self.dir / f'{fmt}.png'
            images.fit(self.picture(source), out, fmt)
            with Image.open(out) as result:
                self.assertEqual(result.size, images.SIZES[fmt])

    def test_fit_refuses_a_crop_that_could_cut_text(self):
        with self.assertRaisesRegex(PlanError, 'would cut'):
            images.fit(self.picture((1024, 1024)), self.dir / 'out.png', 'post')

    def test_fit_allows_the_crop_for_plates_when_asked(self):
        out = self.dir / 'out.png'
        self.assertGreater(images.fit(self.picture((1024, 1024)), out, 'post', allow_crop=True)['cropped'], .1)

    def test_fit_never_overwrites(self):
        out = self.dir / 'out.png'
        out.write_bytes(b'x')
        with self.assertRaises(PlanError):
            images.fit(self.picture((1024, 1280)), out, 'post')

    def test_fit_places_the_logo_in_the_footer_band(self):
        logo = self.dir / 'logo.png'
        Image.new('RGBA', (200, 100), '#FF0000').save(logo)
        out = self.dir / 'out.png'
        images.fit(self.picture((1024, 1280)), out, 'post', logo=logo)
        with Image.open(out) as result:
            self.assertEqual(result.getpixel((540, 1245))[:3], (255, 0, 0))
            self.assertNotEqual(result.getpixel((540, 1100))[:3], (255, 0, 0))

    def test_plate_prompts_forbid_text_and_keep_the_visual_prompt(self):
        for item in images.prompts(self.plan, 'plate'):
            self.assertIn('no text', item['prompt'])
            self.assertIn(self.plan['slides'][item['slide'] - 1]['visual_prompt'], item['prompt'])

    def test_full_prompts_quote_the_exact_copy(self):
        self.plan['slides'][1]['headline'] = 'Şöyle güçlü bir başlık'
        prompt = images.prompts(self.plan, 'full')[1]['prompt']
        self.assertIn('"Şöyle güçlü bir başlık"', prompt)
        self.assertIn('print only the text listed above', prompt)

    def test_prompts_mark_which_slides_need_a_picture(self):
        items = images.prompts(read_json(ROOT / 'examples/photo.json'))
        self.assertTrue(items[0]['needs_image'])
        self.assertFalse(items[1]['needs_image'])


class PlanGate(Workspace):
    def setUp(self):
        super().setUp()
        self.old = project_dir()
        import os
        self.env = os.environ
        self.env['BRANDKING_PROJECT'] = str(self.dir)
        self.addCleanup(self.env.pop, 'BRANDKING_PROJECT', None)

    def test_no_statement_blocks(self):
        with self.assertRaisesRegex(PlanError, 'No plan confirmed'):
            gate.check()

    def test_every_qualifying_plan_passes(self):
        for plan in ('plus', 'pro', 'business', 'edu', 'enterprise', ' Plus '):
            gate.confirm(plan)
            self.assertEqual(gate.check()['plan'], plan.strip().lower())

    def test_free_and_go_are_refused_and_not_recorded(self):
        for plan in ('free', 'go'):
            with self.assertRaisesRegex(PlanError, 'does not qualify'):
                gate.confirm(plan)
        with self.assertRaises(PlanError):
            gate.check()

    def test_unknown_plan_refused(self):
        with self.assertRaises(PlanError):
            gate.confirm('platinum')

    def test_tampered_record_is_refused(self):
        gate.confirm('plus')
        gate.gate_file().write_text('{"plan": "free"}', encoding='utf-8')
        with self.assertRaisesRegex(PlanError, 'does not qualify'):
            gate.check()

    def test_record_admits_it_is_unverified(self):
        self.assertIn('Not verified', gate.confirm('plus')['note'])

    def test_doctor_never_claims_a_verified_plan(self):
        finding = next(f for f in gate.doctor() if f['check'] == 'chatgpt_plan_verified')
        self.assertEqual(finding['severity'], 'skipped')
        self.assertTrue(finding['detail'])

    def test_cli_exit_codes(self):
        self.assertEqual(cli.main(['gate', 'check']), 1)
        self.assertEqual(cli.main(['gate', 'confirm', '--plan', 'free']), 1)
        self.assertEqual(cli.main(['gate', 'confirm', '--plan', 'plus']), 0)
        self.assertEqual(cli.main(['gate', 'check']), 0)

    def test_project_assets_are_found_outside_the_engine(self):
        path = self.dir / 'mine.png'
        Image.new('RGB', (10, 10)).save(path)
        self.assertEqual(asset_path('mine.png'), path.resolve())
        self.assertEqual(asset_path('assets/fonts/Figtree.ttf'), FIGTREE.resolve())
        with self.assertRaises(PlanError):
            asset_path('../outside.png')


class BrandMemory(Workspace):
    def setUp(self):
        super().setUp()
        home = self.dir / 'home'
        project = self.dir / 'project'
        project.mkdir()
        old_home, old_project = os.environ.get('BRANDKING_HOME'), os.environ.get('BRANDKING_PROJECT')
        os.environ['BRANDKING_HOME'] = str(home)
        os.environ['BRANDKING_PROJECT'] = str(project)
        self.addCleanup(os.environ.__setitem__, 'BRANDKING_HOME', old_home)
        self.addCleanup(lambda: os.environ.pop('BRANDKING_PROJECT', None))
        self.home, self.project = home, project

    def save(self, **fields):
        return memory.remember({'name': 'Atelier Noor', 'primary': '#5B2333', 'accent': '#E9B872', **fields})

    def test_nothing_saved_returns_none(self):
        self.assertIsNone(memory.recall())

    def test_recall_returns_the_last_brand_used(self):
        self.save()
        memory.remember({'name': 'Second Brand', 'primary': '#123456', 'accent': '#FFAA00'})
        self.assertEqual(memory.recall()['brand']['name'], 'Second Brand')
        self.assertEqual(memory.recall('atelier-noor')['brand']['name'], 'Atelier Noor')

    def test_memory_survives_across_projects(self):
        self.save()
        other = self.dir / 'other'
        other.mkdir()
        os.environ['BRANDKING_PROJECT'] = str(other)
        self.assertEqual(memory.recall()['slug'], 'atelier-noor')

    def test_two_colors_are_enough(self):
        brand = self.save()['brand']
        for key in ('dark', 'light', 'warm'):
            self.assertRegex(brand[key], '^#[0-9A-F]{6}$')

    def test_update_keeps_what_is_not_given(self):
        self.save(handle='@noor', visual_structure='Quiet still lifes')
        memory.remember({'slug': 'atelier-noor', 'accent': '#FFFFFF'})
        brand = memory.recall()['brand']
        self.assertEqual(brand['accent'], '#FFFFFF')
        self.assertEqual(brand['handle'], '@noor')
        self.assertEqual(brand['visual_structure'], 'Quiet still lifes')

    def test_files_are_copied_so_the_originals_can_move(self):
        logo = self.dir / 'logo.png'
        Image.new('RGBA', (20, 10), '#FF0000').save(logo)
        saved = self.save(logo=str(logo))
        logo.unlink()
        self.assertTrue(asset_path(saved['brand']['logo']).is_file())

    def test_references_are_kept_and_not_duplicated(self):
        ref = self.dir / 'look.png'
        Image.new('RGB', (10, 10)).save(ref)
        self.save()
        memory.remember({'slug': 'atelier-noor'}, [ref])
        memory.remember({'slug': 'atelier-noor'}, [ref])
        self.assertEqual(memory.recall()['brand']['references'], ['brands/atelier-noor/references/look.png'])

    def test_plan_without_a_brand_uses_memory(self):
        self.save()
        del self.plan['brand']
        self.assertEqual(validate(self.plan)[0]['name'], 'Atelier Noor')
        self.plan['brand'] = '@memory'
        self.assertEqual(validate(self.plan)[0]['name'], 'Atelier Noor')
        self.plan['brand'] = '@atelier-noor'
        self.assertEqual(validate(self.plan)[0]['name'], 'Atelier Noor')

    def test_plan_without_any_saved_brand_asks_once(self):
        del self.plan['brand']
        with self.assertRaisesRegex(PlanError, 'Give the brand details once'):
            validate(self.plan)

    def test_passing_render_remembers_an_inline_brand(self):
        self.plan['brand'] = {'name': 'First Use', 'primary': '#183B32', 'accent': '#D6F75A', 'dark': '#111A17',
                              'light': '#F6F7F2', 'warm': '#EDE5D3'}
        result = deliver.render(self.write_plan(), self.dir / 'out')
        self.assertEqual(result['remembered'], 'first-use')
        self.assertEqual(memory.recall()['brand']['name'], 'First Use')

    def test_demo_brands_are_never_remembered(self):
        result = deliver.render(DEMO, self.dir / 'out')
        self.assertIsNone(result['remembered'])
        self.assertIsNone(memory.recall())

    def test_failed_render_does_not_remember(self):
        self.plan['brand'] = {'name': 'Bad Run', 'primary': '#183B32', 'accent': '#D6F75A', 'dark': '#111A17',
                              'light': '#F6F7F2', 'warm': '#EDE5D3'}
        self.plan['slides'][1]['body'] = 'Guaranteed results for everyone.'
        deliver.render(self.write_plan(), self.dir / 'out')
        self.assertIsNone(memory.recall())

    def test_can_opt_out_of_remembering(self):
        self.plan['brand'] = {'name': 'Private', 'primary': '#183B32', 'accent': '#D6F75A', 'dark': '#111A17',
                              'light': '#F6F7F2', 'warm': '#EDE5D3'}
        deliver.render(self.write_plan(), self.dir / 'out', remember=False)
        self.assertIsNone(memory.recall())

    def test_falls_back_to_the_project_when_home_is_not_writable(self):
        blocker = self.dir / 'file-not-folder'
        blocker.write_text('x', encoding='utf-8')
        os.environ['BRANDKING_HOME'] = str(blocker)
        saved = self.save()
        self.assertEqual(saved['scope'], 'project')
        self.assertTrue((self.project / '.brandking/brands/atelier-noor/brand.json').is_file())

    def test_forget_removes_it(self):
        self.save()
        memory.forget('atelier-noor')
        self.assertIsNone(memory.recall())
        self.assertEqual(memory.list_brands(), [])

    def test_forget_cannot_escape(self):
        with self.assertRaises(PlanError):
            memory.forget('../../evil')

    def test_slug_keeps_letters_from_other_languages_readable(self):
        self.assertEqual(memory.slugify('Çiçek & Şüphe'), 'cicek-suphe')

    def test_font_name_and_structure_reach_the_prompts(self):
        self.save(title_font_name='Playfair Display', visual_structure='Single light source, heavy glass')
        del self.plan['brand']
        prompt = images.prompts(self.plan, 'full')[0]['prompt']
        self.assertIn('Playfair Display', prompt)
        self.assertIn('Single light source', prompt)

    def test_command_line_flow(self):
        self.assertEqual(cli.main(['brand', 'recall']), 1)
        self.assertEqual(cli.main(['brand', 'remember', '--name', 'Atelier Noor', '--primary', '#5B2333', '--accent', '#E9B872',
                                   '--title-font-name', 'Playfair Display', '--visual-structure', 'Quiet', '--tone', 'Calm',
                                   '--banned-word', 'cheap']), 0)
        self.assertEqual(cli.main(['brand', 'recall', '--json']), 0)
        self.assertEqual(memory.recall()['brand']['voice']['banned_words'], ['cheap'])
        self.assertEqual(cli.main(['brand', 'list']), 0)
        self.assertEqual(cli.main(['brand', 'forget', 'atelier-noor']), 0)


class CodexPackage(unittest.TestCase):
    def test_versions_agree(self):
        from brandking import __version__
        self.assertEqual(read_json(ROOT / '.codex-plugin/plugin.json')['version'], __version__)

    def test_marketplace_points_at_the_plugin(self):
        market = read_json(ROOT / '.agents/plugins/marketplace.json')
        entry = market['plugins'][0]
        self.assertEqual(entry['name'], read_json(ROOT / '.codex-plugin/plugin.json')['name'])
        self.assertTrue(entry['source']['path'].startswith('./'))
        for key in ('installation', 'authentication'):
            self.assertIn(key, entry['policy'])
        self.assertIn('category', entry)

    def test_every_skill_has_name_and_description(self):
        skills = sorted((ROOT / 'skills').glob('*/SKILL.md'))
        self.assertGreaterEqual(len(skills), 3)
        for path in skills:
            head = path.read_text(encoding='utf-8').split('---')[1]
            self.assertIn(f'name: {path.parent.name}', head)
            self.assertIn('description: ', head)

    def test_director_keeps_the_plan_gate_and_refuses_api_keys(self):
        text = (ROOT / 'skills/brandking-director/SKILL.md').read_text(encoding='utf-8')
        for phrase in ('ChatGPT Plus or higher', 'gate check', 'Never use the `OPENAI_API_KEY`', '$imagegen', 'letter by letter'):
            self.assertIn(phrase, text)

    def test_files_named_in_the_manifest_exist(self):
        interface = read_json(ROOT / '.codex-plugin/plugin.json')['interface']
        for key in ('composerIcon', 'logo'):
            self.assertTrue((ROOT / interface[key]).is_file(), key)

    def test_guides_named_by_the_skill_exist(self):
        text = (ROOT / 'skills/brandking-director/SKILL.md').read_text(encoding='utf-8')
        import re
        for name in set(re.findall(r'guides/[\w-]+\.md', text)):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_codex_agents_match_their_source(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('sync_agents', ROOT / 'scripts/sync_codex_agents.py')
        sync = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sync)
        expected = sync.expected()
        self.assertEqual(len(expected), 6)
        for name, content in expected.items():
            self.assertEqual((ROOT / '.codex/agents' / name).read_text(encoding='utf-8'), content, name)

    def test_codex_agents_are_valid_toml(self):
        try:
            import tomllib
        except ImportError:
            self.skipTest('tomllib needs Python 3.11')
        for path in (ROOT / '.codex/agents').glob('*.toml'):
            data = tomllib.loads(path.read_text(encoding='utf-8'))
            for key in ('name', 'description', 'developer_instructions'):
                self.assertTrue(data[key], path.name)

    def test_reference_images_are_not_shipped(self):
        self.assertEqual(list(ROOT.glob('**/WhatsApp Image*')), [])


class CommandLine(Workspace):
    def test_exit_codes(self):
        self.assertEqual(cli.main(['check', str(DEMO)]), 0)
        self.plan['slides'][1]['body'] = 'Guaranteed results for everyone.'
        self.assertEqual(cli.main(['check', str(self.write_plan())]), 1)

    def test_bad_plan_exits_one(self):
        self.plan['slides'][0]['layout'] = 'unknown'
        self.assertEqual(cli.main(['lint', str(self.write_plan())]), 1)

    def test_layouts_lists_everything(self):
        self.assertEqual(cli.main(['layouts', '--json']), 0)


if __name__ == '__main__':
    unittest.main()
