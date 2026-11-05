import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from PIL import Image
import carousel


class CarouselTests(unittest.TestCase):
    def setUp(self):
        self.plan = carousel.read_json(carousel.ROOT/'examples/demo.json')
        (carousel.ROOT/'outputs').mkdir(exist_ok=True)

    def test_full_delivery(self):
        with tempfile.TemporaryDirectory(prefix='carousel test ', dir=carousel.ROOT/'outputs') as temp:
            out = Path(temp)/'delivery'
            carousel.render(carousel.ROOT/'examples/demo.json', out)
            self.assertEqual(len(list((out/'slides').glob('*.png'))), 6)
            for path in (out/'slides').glob('*.png'):
                with Image.open(path) as im:
                    self.assertEqual(im.size, (1080, 1350))
                    self.assertGreater(len(im.getcolors(2**24)), 20)
            with zipfile.ZipFile(out/'carousel.zip') as archive:
                self.assertIn('slides/01.png', archive.namelist())
                self.assertIn('editable/recipe/carousel.py', archive.namelist())
                self.assertIn('editable/recipe/assets/fonts/Figtree.ttf', archive.namelist())
            report = carousel.read_json(out/'qa-report.json')
            self.assertEqual(report['automatic'], 'passed')
            self.assertEqual(report['visual'], 'pending')
            with self.assertRaises(ValueError):
                carousel.render(carousel.ROOT/'examples/demo.json', out)

    def test_long_headline_rejected(self):
        self.plan['slides'][0]['headline'] = 'This headline has far too many words for reading'
        with self.assertRaises(ValueError):
            carousel.validate(self.plan)

    def test_repeated_layout_rejected(self):
        self.plan['slides'][1]['layout'] = 'cover'
        with self.assertRaises(ValueError):
            carousel.validate(self.plan)

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            carousel.asset_path('../outside.png')

    def test_missing_image_rejected(self):
        self.plan['slides'][1]['image'] = 'missing.png'
        with self.assertRaises(ValueError):
            carousel.validate(self.plan)

    def test_low_contrast_rejected(self):
        path = carousel.ROOT/'assets/fonts/Figtree.ttf'
        c = carousel.Canvas('#FFFFFF', path, path)
        with self.assertRaises(ValueError):
            c.text('Invisible', (96, 100, 984, 400), 48, '#EEEEEE', '#FFFFFF')

    def test_overflow_rejected(self):
        path = carousel.ROOT/'assets/fonts/Figtree.ttf'
        c = carousel.Canvas('#FFFFFF', path, path)
        with self.assertRaises(ValueError):
            c.text('Too much text in a tiny area', (96, 100, 200, 110), 48, '#111111', '#FFFFFF')

    def test_unicode_and_xml_escaping(self):
        path, title = carousel.validate(self.plan)
        c = carousel.Canvas('#FFFFFF', path, title)
        c.text('İ ı Ç ç Ğ ğ Ö ö Ş ş Ü ü < & >', (96, 100, 984, 400), 36, '#111111', '#FFFFFF')
        self.assertIn('&lt;', ''.join(c.svg))
        self.assertIn('&amp;', ''.join(c.svg))

    def test_second_brand_changes_output(self):
        path, title = carousel.validate(self.plan)
        s = self.plan['slides'][0]
        first = carousel.render_slide(s, self.plan['brand'], 1, 6, path, title)
        brand = copy.deepcopy(self.plan['brand'])
        brand.update(primary='#3B1835', accent='#FFDCA8', name='SECOND BRAND')
        second = carousel.render_slide(s, brand, 1, 6, path, title)
        self.assertNotEqual(first.im.tobytes(), second.im.tobytes())

    def test_product_photo_preserves_aspect_ratio(self):
        path, title = carousel.validate(self.plan)
        with tempfile.TemporaryDirectory(dir=carousel.ROOT/'outputs') as temp:
            photo = Path(temp)/'product.png'
            Image.new('RGBA', (200, 100), '#FF0000').save(photo)
            c = carousel.Canvas('#FFFFFF', path, title)
            c.image(photo, (100, 400, 500, 800))
            self.assertEqual(c.im.getpixel((200, 450)), (255, 255, 255))
            self.assertEqual(c.im.getpixel((200, 550)), (255, 0, 0))


if __name__ == '__main__':
    unittest.main()
