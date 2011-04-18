from unittest import TestCase
from cStringIO import StringIO

from scrapely import Scraper

class ScraperTest(TestCase):

    def test_train_store_load_scrape(self):
        url1 = 'http://www.icone.co.uk/lighting-suspension/copper-shade-by-tom-dixon/tom-dixon/tom-dixon/MSS45UKC/'
        data = {'name': 'Copper Shade by Tom Dixon', 'designer': 'Tom Dixon', 'price': '320'}
        s = Scraper()
        s.train(url1, data, encoding='latin1')

        f = StringIO()
        s.tofile(f)

        f.seek(0)
        s = Scraper.fromfile(f)

        url2 = 'http://www.icone.co.uk/lighting-wall-and-ceiling/mesmeri-halo-chrome/artemide/eric-sole/0916024A/'
        data = s.scrape(url2, encoding='latin1')
        self.assertEqual(sorted(data[0].keys()), ['designer', 'name', 'price'])
