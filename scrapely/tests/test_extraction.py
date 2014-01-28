# -*- coding: utf-8 -*-
"""
tests for page parsing

Page parsing effectiveness is measured through the evaluation system. These
tests should focus on specific bits of functionality work correctly.
"""
from unittest import TestCase
from nose_parameterized import parameterized
from scrapely.extraction.similarity import first_longest_subsequence

from scrapely.htmlpage import HtmlPage
from scrapely.descriptor import (FieldDescriptor as A,
        ItemDescriptor)
from scrapely.extractors import (contains_any_numbers,
        image_url, html, notags, text, extract_price)
from scrapely.extraction import InstanceBasedLearningExtractor, BasicTypeExtractor, TraceExtractor, RecordExtractor, TemplatePageExtractor
from scrapely.tests import get_page

# simple page with all features

ANNOTATED_PAGE1 = u"""
<html>
<h1>COMPANY - <ins
    data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;generated&quot;: true,
    &quot;annotations&quot;: {&quot;content&quot;: &quot;title&quot;}}"
>Item Title</ins></h1>
<p>introduction</p>
<div>
<img data-scrapy-annotate="{&quot;variant&quot;: 0,
    &quot;annotations&quot;: {&quot;src&quot;: &quot;image_url&quot;}}"
    src="img.jpg"/>
<p data-scrapy-annotate="{&quot;variant&quot;: 0,
    &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">
This is such a nice item<br/> Everybody likes it.
</p>
<br/>
</div>
<p>click here for other items</p>
</html>
"""

EXTRACT_PAGE1 = u"""
<html>
<h1>Scrapy - Nice Product</h1>
<p>introduction</p>
<div>
<img src="nice_product.jpg" alt="a nice product image"/>
<p>wonderful product</p>
<br/>
</div>
</html>
"""

# single tag with multiple items extracted
ANNOTATED_PAGE2 = u"""
<a href="http://example.com/xxx" title="xxx"
    data-scrapy-annotate="{&quot;variant&quot;: 0,
    &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;,
        &quot;href&quot;: &quot;image_url&quot;, &quot;title&quot;: &quot;name&quot;}}"
>xx</a>
xxx
</a>
"""
EXTRACT_PAGE2 = u"""<a href='http://example.com/product1.jpg'
    title="product 1">product 1 is great</a>"""

# matching must match the second attribute in order to find the first
ANNOTATED_PAGE3 = u"""
<p data-scrapy-annotate="{&quot;variant&quot;: 0,
    &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">xx</p>
<div data-scrapy-annotate="{&quot;variant&quot;: 0,
    &quot;annotations&quot;: {&quot;content&quot;: &quot;delivery&quot;}}">xx</div>
"""
EXTRACT_PAGE3 = u"""
<p>description</p>
<div>delivery</div>
<p>this is not the description</p>
"""

# test inferring repeated elements
ANNOTATED_PAGE4 = u"""
<ul>
<li data-scrapy-annotate="{&quot;variant&quot;: 0,
    &quot;annotations&quot;: {&quot;content&quot;: &quot;features&quot;}}">feature1</li>
<li data-scrapy-annotate="{&quot;variant&quot;: 0,
    &quot;annotations&quot;: {&quot;content&quot;: &quot;features&quot;}}">feature2</li>
</ul>
"""

EXTRACT_PAGE4 = u"""
<ul>
<li>feature1</li> ignore this
<li>feature2</li>
<li>feature3</li>
</ul>
"""

# test variant handling with identical repeated variant
ANNOTATED_PAGE5 =  u"""
<p data-scrapy-annotate="{&quot;annotations&quot;:
    {&quot;content&quot;: &quot;description&quot;}}">description</p>
<table>
<tr>
<td data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;colour&quot;}}" >colour 1</td>
<td data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;price&quot;}}" >price 1</td>
</tr>
<tr>
<td data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;colour&quot;}}" >colour 2</td>
<td data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;price&quot;}}" >price 2</td>
</tr>
</table>
"""

ANNOTATED_PAGE5a =  u"""
<p data-scrapy-annotate="{&quot;annotations&quot;:
    {&quot;content&quot;: &quot;description&quot;}}">description</p>
<table>
<tr>
<td data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;colour&quot;}}" >colour 1</td>
<td data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;price&quot;}, &quot;required&quot;: [&quot;price&quot;]}" >price 1</td>
</tr>
<tr>
<td data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;colour&quot;}}" >colour 2</td>
<td data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;price&quot;}, &quot;required&quot;: [&quot;price&quot;]}" >price 2</td>
</tr>
</table>
"""

EXTRACT_PAGE5 = u"""
<p>description</p>
<table>
<tr>
<td>colour 1</td>
<td>price 1</td>
</tr>
<tr>
<td>colour 2</td>
<td>price 2</td>
</tr>
<tr>
<td>colour 3</td>
<td>price 3</td>
</tr>
</table>
"""

# test variant handling with irregular structure and some non-variant
# attributes
ANNOTATED_PAGE6 =  u"""
<p data-scrapy-annotate="{&quot;annotations&quot;:
    {&quot;content&quot;: &quot;description&quot;}}">description</p>
<p data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;name&quot;}}">name 1</p>
<div data-scrapy-annotate="{&quot;variant&quot;: 3, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;name&quot;}}" >name 3</div>
<p data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;name&quot;}}" >name 2</p>
"""
EXTRACT_PAGE6 =  u"""
<p>description</p>
<p>name 1</p>
<div>name 3</div>
<p>name 2</p>
"""

# test repeating variants at the table column level
ANNOTATED_PAGE7 =  u"""
<table>
<tr>
<td data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;colour&quot;}}" >colour 1</td>
<td data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;colour&quot;}}" >colour 2</td>
</tr>
<tr>
<td data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;price&quot;}}" >price 1</td>
<td data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;annotations&quot;:
    {&quot;content&quot;: &quot;price&quot;}}" >price 2</td>
</tr>
</table>
"""

EXTRACT_PAGE7 = u"""
<table>
<tr>
<td>colour 1</td>
<td>colour 2</td>
<td>colour 3</td>
</tr>
<tr>
<td>price 1</td>
<td>price 2</td>
<td>price 3</td>
</tr>
</table>
"""

ANNOTATED_PAGE8 = u"""
<html><body>
<h1>A product</h1>
<div data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">
<p>XXXX XXXX xxxxx</p>
<div data-scrapy-ignore="true">
<img scr="image.jpg" /><br/><a link="back.html">Click here to go back</a>
</div>
</div>
<div data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">
10.00<p data-scrapy-ignore="true"> 13</p>
</div>
</body></html>
"""

EXTRACT_PAGE8 = u"""
<html><body>
<h1>A product</h1>
<div>
<p>A very nice product for all intelligent people</p>
<div>
<img scr="image.jpg" /><br/><a link="back.html">Click here to go back</a>
</div>
</div>
<div>
12.00<p> ID 15</p>
(VAT exc.)</div>
</body></html>
"""

ANNOTATED_PAGE9 = ANNOTATED_PAGE8

EXTRACT_PAGE9 = u"""
<html><body>
<img src="logo.jpg" />
<h1>A product</h1>
<div>
<p>A very nice product for all intelligent people</p>
<div>
<img scr="image.jpg" /><br/><a link="back.html">Click here to go back</a>
</div>
</div>
<div>
12.00<p> ID 16</p>
(VAT exc.)</div>
</body></html>
"""

ANNOTATED_PAGE11 = u"""
<html><body>
<p data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">
<ins data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;generated&quot;: true,
    &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">
SL342
</ins>
<br/>
Nice product for ladies
<br/><ins data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;generated&quot;: true,
     &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">
&pound;85.00
</ins>
</p>
<ins data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;generated&quot;: true,
     &quot;annotations&quot;: {&quot;content&quot;: &quot;price_before_discount&quot;}}">
&pound;100.00
</ins>
</body></html>
"""

EXTRACT_PAGE11 = u"""
<html><body>
<p>
SL342
<br/>
Nice product for ladies
<br/>
&pound;85.00
</p>
&pound;100.00
</body></html>
"""

ANNOTATED_PAGE12 = u"""
<html><body>
<h1 data-scrapy-ignore-beneath="true">A product</h1>
<div data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">
<p>XXXX XXXX xxxxx</p>
<div data-scrapy-ignore-beneath="true">
<img scr="image.jpg" /><br/><a link="back.html">Click here to go back</a>
</div>
<div>
10.00<p> 13</p>
</div>
</div>
</body></html>
"""

EXTRACT_PAGE12a = u"""
<html><body>
<h1>A product</h1>
<div>
<p>A very nice product for all intelligent people</p>
<div>
<img scr="image.jpg" /><br/><a link="back.html">Click here to go back</a>
</div>
<div>
12.00<p> ID 15</p>
(VAT exc.)
</div></div>
</body></html>
"""

EXTRACT_PAGE12b = u"""
<html><body>
<h1>A product</h1>
<div>
<p>A very nice product for all intelligent people</p>
<div>
<img scr="image.jpg" /><br/><a link="back.html">Click here to go back</a>
</div>
<div>
12.00<p> ID 15</p>
(VAT exc.)
</div>
<ul>
Features
<li>Feature A</li>
<li>Feature B</li>
</ul>
</div>
</body></html>
"""

# Ex1: nested annotation with token sequence replica outside exterior annotation
# and a possible sequence pattern can be extracted only with
# correct handling of nested annotations
ANNOTATED_PAGE13a = u"""
<html><body>
<span>
<p data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">
<hr/>
<h3 data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">A product</h3>
<b data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">$50.00</b>
This product is excelent. Buy it!
</p>
</span>
<span>
<p>
<h3>See other products:</h3>
<b>Product b</b>
</p>
</span>
<hr/>
</body></html>
"""

EXTRACT_PAGE13a = u"""
<html><body>
<span>
<p>
<h3>A product</h3>
<b>$50.00</b>
This product is excelent. Buy it!
<hr/>
</p>
</span>
<span>
<p>
<h3>See other products:</h3>
<b>Product B</b>
</p>
</span>
</body></html>
"""

# Ex2: annotation with token sequence replica inside a previous nested annotation
# and a possible sequence pattern can be extracted only with
# correct handling of nested annotations
ANNOTATED_PAGE13b = u"""
<html><body>
<span>
<p data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">
<h3 data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">A product</h3>
<b>Previous price: $50.00</b>
This product is excelent. Buy it!
</p>
</span>
<span>
<p>
<h3>Save 10%!!</h3>
<b data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">$45.00</b>
</p>
</span>
</body></html>
"""

EXTRACT_PAGE13b = u"""
<html><body>
<span>
<p>
<h3>A product</h3>
<b>$50.00</b>
This product is excelent. Buy it!
</p>
</span>
<span>
<hr/>
<p>
<h3>Save 10%!!</h3>
<b>$45.00</b>
</p>
</span>
<hr/>
</body></html>
"""

ANNOTATED_PAGE14 = u"""
<html><body>
<b data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}"></b>
<p data-scrapy-ignore="true"></p>
</body></html>
"""

EXTRACT_PAGE14 = u"""
<html><body>
</body></html>
"""

ANNOTATED_PAGE15 = u"""
<html><body>
<div data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;short_description&quot;}}">Short
<div data-scrapy-ignore="true" data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;site_id&quot;}}">892342</div>
</div>
<hr/>
<p data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">Description
<b data-scrapy-ignore="true" data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">90.00</b>
</p>
</body></html>
"""

EXTRACT_PAGE15 = u"""
<html><body>
<hr/>
<p>Description
<b>80.00</b>
</p>
</body></html>
"""

ANNOTATED_PAGE16 = u"""
<html><body>
<div data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">
Description
<p data-scrapy-ignore="true" data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">
name</p>
<p data-scrapy-ignore="true" data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">
80.00</p>
</div>
</body></html>
"""

EXTRACT_PAGE16 = u"""
<html><body>
<p>product name</p>
<p>90.00</p>
</body></html>
"""

ANNOTATED_PAGE17 = u"""
<html><body>
<span>
<p data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">
This product is excelent. Buy it!
</p>
</span>
<table></table>
<img src="line.jpg" data-scrapy-ignore-beneath="true"/>
<span>
<h3>See other products:</h3>
<p>Product b
</p>
</span>
</body></html>
"""

EXTRACT_PAGE17 = u"""
<html><body>
<span>
<p>
This product is excelent. Buy it!
</p>
</span>
<img src="line.jpg"/>
<span>
<h3>See other products:</h3>
<p>Product B
</p>
</span>
</body></html>
"""

ANNOTATED_PAGE18 = u"""
<html><body>
<div data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">
<ins data-scrapy-ignore="true" data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;generated&quot;: true, &quot;annotations&quot;: {&quot;content&quot;: &quot;site_id&quot;}}">Item Id</ins>
<br>
Description
</div>
</body></html>
"""

EXTRACT_PAGE18 = u"""
<html><body>
<div>
Item Id
<br>
Description
</div>
</body></html>
"""

ANNOTATED_PAGE19 = u"""
<html><body>
<div>
<p data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">Product name</p>
<p data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">60.00</p>
<img data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;src&quot;: &quot;image_urls&quot;}}" src="image.jpg" />
<p data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;required&quot;: [&quot;description&quot;], &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">description</p>
</div>
</body></html>
"""

EXTRACT_PAGE19a = u"""
<html><body>
<div>
<p>Product name</p>
<p>60.00</p>
<img src="http://example.com/image.jpg" />
<p>description</p>
</div>
</body></html>
"""

EXTRACT_PAGE19b = u"""
<html><body>
<div>
<p>Range</p>
<p>from 20.00</p>
<img src="http://example.com/image1.jpg" />
<p>
<br/>
</div>
</body></html>
"""

ANNOTATED_PAGE20 = u"""
<html><body>
<h1>Product Name</h1>
<img src="product.jpg">
<br/>
<span><ins data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">Twin</ins>:</span> $<ins data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">270</ins> - November 2010<br/>
<span><ins data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">Queen</ins>:</span> $<ins data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">330</ins> - In stock<br/>
<br/>
</body></html>
"""

EXTRACT_PAGE20 = u"""
<html><body>
<h1>Product Name</h1>
<img src="product.jpg">
<br/>
<span>Twin:</span> $270 - November 2010<br/>
<span>Queen:</span> $330 - Movember 2010<br/>
<br/>
</body></html>
"""

ANNOTATED_PAGE21 = u"""
<html><body>
<img src="image.jpg" data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;src&quot;: &quot;image_urls&quot;}}">
<p>
<table>

<tr><td><img src="swatch1.jpg" data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 1, &quot;annotations&quot;: {&quot;src&quot;: &quot;swatches&quot;}}"></td></tr>

<tr><td><img src="swatch2.jpg"></td></tr>

<tr><td><img src="swatch3.jpg"></td></tr>

<tr><td><img src="swatch4.jpg" data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 2, &quot;annotations&quot;: {&quot;src&quot;: &quot;swatches&quot;}}"></td></tr>

</table>

<div data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;category&quot;}}">tables</div>

</body></html>
"""

EXTRACT_PAGE21 = u"""
<html><body>
<img src="image.jpg">
<p>
<table>

<tr><td><img src="swatch1.jpg"></td></tr>

<tr><td><img src="swatch2.jpg"></td></tr>

<tr><td><img src="swatch3.jpg"></td></tr>

<tr><td><img src="swatch4.jpg"></td></tr>

</table>

<div>chairs</div>
</body></html>
"""

ANNOTATED_PAGE22 = u"""
<html><body>
<img src="image.jpg" data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;src&quot;: &quot;image_urls&quot;}}">
<p>
<table>

<tr><td>
<p data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 1, &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">product 1</p>
<b data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 1, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">$67</b>
<img src="swatch1.jpg" data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 1, &quot;annotations&quot;: {&quot;src&quot;: &quot;swatches&quot;}}">
</td></tr>

<tr><td>
<p>product 2</p>
<b>$70</b>
<img src="swatch2.jpg">
</td></tr>

<tr><td>
<p>product 3</p>
<b>$73</b>
<img src="swatch3.jpg">
</td></tr>

<tr><td>
<p data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 2, &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">product 4</p>
<b data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 2, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">$80</b>
<img src="swatch4.jpg" data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 2, &quot;annotations&quot;: {&quot;src&quot;: &quot;swatches&quot;}}">
</td></tr>

</table>

<div data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;category&quot;}}">tables</div>

</body></html>
"""

EXTRACT_PAGE22 = u"""
<html><body>
<img src="image.jpg">
<p>
<table>

<tr><td>
<p>product 1</p>
<b>$70</b>
<img src="swatch1.jpg">
</td></tr>

<tr><td>
<p>product 2</p>
<b>$80</b>
<img src="swatch2.jpg">
</td></tr>

<tr><td>
<p>product 3</p>
<b>$90</b>
<img src="swatch3.jpg">
</td></tr>

<tr><td>
<p>product 4</p>
<b>$100</b>
<img src="swatch4.jpg">
</td></tr>

</table>

<div>chairs</div>
</body></html>
"""

ANNOTATED_PAGE23 = u"""
<html><body>
<h4>Product</h4>
<table>
<tr><td>
<p data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 1, &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">Variant 1<b data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 1, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}" data-scrapy-ignore="true">560</b></p>
</td></tr>
<tr><td>
<p>Variant 2<b>570</b></p>
</td></tr>
<tr><td>
<p data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 2, &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">Variant 3<b data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 2, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}" data-scrapy-ignore="true">580</b></p>
</td></tr>
</table>
</body></html>
"""

EXTRACT_PAGE23 = u"""
<html><body>
<h4>Product</h4>
<table>
<tr><td>
<p>Variant 1<b>300</b></p>
</td></tr>
<tr><td>
<p>Variant 2<b>320</b></p>
</td></tr>
<tr><td>
<p>Variant 3<b>340</b></p>
</td></tr>
</table>
</body></html>
"""

ANNOTATED_PAGE24 = u"""
<html><body>
<h1 data-scrapy-ignore-beneath="true">A product</h1>
<div data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">
<p>XXXX XXXX xxxxx</p>
<div data-scrapy-ignore-beneath="true">
<img scr="image.jpg" /><br/><a link="back.html">Click here to go back</a>
</div>
<p data-scrapy-ignore-beneath="true">Important news!!</p>
<div>
10.00<p> 13</p>
</div>
</div>
</body></html>
"""

EXTRACT_PAGE24 = u"""
<html><body>
<h1>A product</h1>
<div>
<p>A very nice product for all intelligent people</p>
<div>
<img scr="image.jpg" /><br/><a link="back.html">Click here to go back</a>
</div>
<p>Important news!!</p>
<div>
12.00<p> ID 15</p>
(VAT exc.)
</div></div>
</body></html>
"""

ANNOTATED_PAGE25 = u"""
<span>
<br>
<input type="radio" name="size" checked value='44'>
<ins data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">"Large"</ins>
<br>
<input type="radio" name="size" checked value='45'>
"X Large"
<br>
<input type="radio" name="size" checked value='46'>
<ins data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">"XX Large"</ins>
</span>
"""


EXTRACT_PAGE25 = u"""
<span>
<br>
<input type="radio" name="size" checked value='44'>
"Large"
<br>
<input type="radio" name="size" checked value='45'>
"X Large"
<br>
<input type="radio" name="size" checked value='46'>
"XX Large"
</span>
"""

ANNOTATED_PAGE26 = u"""
<span>
<br>
<input type="radio" name="size" checked value='44'>
<ins data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">"Large"</ins>
<br>
<input type="radio" name="size" checked value='45'>
"X Large"
<br>
<input type="radio" name="size" checked value='46'>
<ins data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">"XX Large"</ins>
</span>
"""

EXTRACT_PAGE26 = u"""
<span>
<br>
<input type="radio" name="size" checked value='44'>
"Large"
<br>
<input type="radio" name="size" checked value='45'>
"X Large"
<br>
<input type="radio" name="size" checked value='46'>
"XX Large"
</span>
"""

ANNOTATED_PAGE27 = u"""
<span>
<br>
<input type="radio" name="size" checked value='44' data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: false,
&quot;annotations&quot;: {&quot;value&quot;: &quot;site_id&quot;}}">
<ins data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">"Large"</ins>
<br>
<input type="radio" name="size" checked value='45'>
"X Large"
<br>
<input type="radio" name="size" checked value='46' data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: false,
&quot;annotations&quot;: {&quot;value&quot;: &quot;site_id&quot;}}">
<ins data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">"XX Large"</ins>
</span>
"""

EXTRACT_PAGE27 = u"""
<span>
<br>
<input type="radio" name="size" checked value='44'>
"Large"
<br>
<input type="radio" name="size" checked value='45'>
"X Large"
<br>
<input type="radio" name="size" checked value='46'>
"XX Large"
</span>
"""

ANNOTATED_PAGE28 = u"""
<span>
<br>
<input type="radio" name="size" checked value='44' data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: false,
&quot;annotations&quot;: {&quot;value&quot;: &quot;site_id&quot;}}">
<ins data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">"Large"</ins>
<br>
<input type="radio" name="size" checked value='45'>
"X Large"
<br>
<input type="radio" name="size" checked value='46' data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: false,
&quot;annotations&quot;: {&quot;value&quot;: &quot;site_id&quot;}}">
<ins data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: true,
&quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">"XX Large"</ins>
</span>
<div data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;generated&quot;: false,
&quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">Price: 45</div>
"""

EXTRACT_PAGE28 = u"""
<span>
<br>
<input type="radio" name="size" checked value='44'>
"Large"
<br>
<input type="radio" name="size" checked value='45'>
"X Large"
<br>
<input type="radio" name="size" checked value='46'>
"XX Large"
</span>
<div>Price: 45</div>
"""

ANNOTATED_PAGE29 = u"""
<table>
<tr><td data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: false,
 &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">Name 1</td><td data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: false,
 &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">Desc 1</td><td><span data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: false,
 &quot;annotations&quot;: {&quot;content&quot;: &quot;tag&quot;}}">Tag 1</span><span>Tag2</span><span data-scrapy-annotate="{&quot;variant&quot;: 1, &quot;generated&quot;: false,
 &quot;annotations&quot;: {&quot;content&quot;: &quot;tag&quot;}}">Tag 3</span></td></tr>
<tr><td>Name 2</td><td>Desc 2</td><td><span>Tag 7</span><span>Tag 8</span></span>Tag 9</span></td></tr>
<tr><td data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: false,
 &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">Name 3</td><td data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: false,
 &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">Desc 3</td><td><span data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: false,
 &quot;annotations&quot;: {&quot;content&quot;: &quot;tag&quot;}}">Tag 4</span><span>Tag5</span><span data-scrapy-annotate="{&quot;variant&quot;: 2, &quot;generated&quot;: false,
 &quot;annotations&quot;: {&quot;content&quot;: &quot;tag&quot;}}">Tag 6</span></td></tr>
</table>
"""

EXTRACT_PAGE29 = u"""
<table>
<tr><td>Name 1</td><td>Desc 1</td><td><span>Tag 1</span><span>Tag 2</span><span>Tag 3</span></td></tr>
<tr><td>Name 2</td><td>Desc 2</td><td><span>Tag 4</span><span>Tag 5</span><span>Tag 6</span></td></tr>
<tr><td>Name 3</td><td>Desc 3</td><td><span>Tag 7</span><span>Tag 8</span><span>Tag 9</span></td></tr>
</table>
"""

ANNOTATED_PAGE30 = u"""
<div data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;generated&quot;: false,
 &quot;annotations&quot;: {&quot;content&quot;: &quot;phone&quot;}}"><span>029349293</span></div>
"""

EXTRACT_PAGE30a = u"""
<div><span style="font-size:100%">Any text</span></div>
"""

EXTRACT_PAGE30b = u"""
<div><span style="font-size:100%">029847272</span></div>
"""

EXTRACT_PAGE30c = u"""
<div><span><!--item no. 100--></span></div>
"""

EXTRACT_PAGE30d = u"""
<div><span><script>var myvar= 10;</script></span></div>
"""

ANNOTATED_PAGE31 = u"""
<html><body>
<div>
<span data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;name&quot;}}">Product name</span>
<div><p data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;price&quot;}}">60.00</p>
<span data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;description&quot;}}">description</span>
<span data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;features&quot;}}">features</span>
<img data-scrapy-annotate="{&quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;src&quot;: &quot;image_urls&quot;}}" src="image.jpg" />
<table></table>
</div></div>
</body></html>
"""

EXTRACT_PAGE31 = u"""
<html><body>
<div>
<span>Product name</span>
<div><p>60.00</p>
<img src="http://example.com/image.jpg" />
<table></table>
</div></div>
</body></html>
"""

# repeated elements with ignored region only in one of them
ANNOTATED_PAGE32 = u"""
<ul>
<li data-scrapy-annotate="{&quot;variant&quot;: 0,
    &quot;annotations&quot;: {&quot;content&quot;: &quot;features&quot;}}">feature1<span data-scrapy-ignore="true"> ignore this</span></li>
<li data-scrapy-annotate="{&quot;variant&quot;: 0,
    &quot;annotations&quot;: {&quot;content&quot;: &quot;features&quot;}}">feature2</li>
</ul>
"""

EXTRACT_PAGE32 = u"""
<ul>
<li>feature1<span> ignore this</span></li>
<li>feature2</li>
<li>feature3</li>
</ul>
"""

ANNOTATED_PAGE33, EXTRACT_PAGE33 = get_page('annotated_page_33'), get_page('extract_page_33')

ANNOTATED_PAGE34, EXTRACT_PAGE34A, EXTRACT_PAGE34B = get_page('annotated_page_34'), \
                                                     get_page('extract_page_34a'), \
                                                     get_page('extract_page_34b')

ANNOTATED_PAGE35, EXTRACT_PAGE35A = get_page('annotated_page_35'), get_page('extract_page_35a')

ANNOTATED_PAGE37, EXTRACT_PAGE37A = get_page('annotated_page_37'), get_page('extract_page_37a')

DEFAULT_DESCRIPTOR = ItemDescriptor('test',
        'item test, removes tags from description attribute',
        [A('description', 'description field without tags', notags)])

SAMPLE_DESCRIPTOR1 = ItemDescriptor('test', 'product test', [
            A('name', "Product name", required=True),
            A('price', "Product price, including any discounts and tax or vat",
                contains_any_numbers, True),
            A('image_urls', "URLs for one or more images", image_url, True),
            A('description', "The full description of the product", html),
            ]
        )

SAMPLE_DESCRIPTOR1a = ItemDescriptor('test', 'product test', [
            A('name', "Product name"),
            A('price', "Product price, including any discounts and tax or vat",
                contains_any_numbers),
            A('image_urls', "URLs for one or more images", image_url),
            A('description', "The full description of the product", html),
            ]
        )

SAMPLE_DESCRIPTOR2 = ItemDescriptor('test', 'item test', [
        A('description', 'description field without tags', notags),
        A('price', "Product price, including any discounts and tax or vat",
                contains_any_numbers),
    ])

SAMPLE_DESCRIPTOR3 = ItemDescriptor('test',
        'item test',
        [A('phone', 'phone number', lambda x: contains_any_numbers(x.text_content))])

SAMPLE_DESCRIPTOR4 =  ItemDescriptor('test',
        'item test, removes tags from description attribute',
        [A('description', 'description field without tags', lambda x: x.text_content)])

SAMPLE_DESCRIPTOR33 =  ItemDescriptor('test', 'class test', [
    A('date', 'date', text),
    A('author', 'author', text),
    A('text', 'text', text)])

PAGE34_DESCRIPTOR =  ItemDescriptor('test', 'class test', [
    A('1_image', '1_image', image_url),
    A('1_price', 'price', extract_price),
    A('1_description', 'text', text)])

PAGE35_DESCRIPTOR =  ItemDescriptor('test', 'class test', [
    A('bild', 'image', image_url),
    A('beschreibung', 'description', text),
    A('titel', 'title', text),
    A('preis', 'price', extract_price),
    A('rabattpreis', 'price', extract_price)])

PAGE37_DESCRIPTOR =  ItemDescriptor('test', 'class test', [
    A('Imagem', 'image', image_url),
    A('Nome', 'name', text),
    A('Preco', 'price', extract_price)])

# A list of (test name, [templates], page, extractors, expected_result)
TEST_DATA = [
    # extract from a similar page
    ('similar page extraction', [ANNOTATED_PAGE1], EXTRACT_PAGE1, DEFAULT_DESCRIPTOR,
        {u'title': [u'Nice Product'], u'description': [u'wonderful product'],
            u'image_url': [u'nice_product.jpg']}
    ),
    # strip the first 5 characters from the title
    ('extractor test', [ANNOTATED_PAGE1], EXTRACT_PAGE1,
        ItemDescriptor('test', 'product test',
            [A('title', "something about a title", lambda x: x[5:])]),
        {u'title': [u'Product'], u'description': [u'wonderful product'],
            u'image_url': [u'nice_product.jpg']}
    ),
    # compilicated tag (multiple attributes and annotation)
    ('multiple attributes and annotation', [ANNOTATED_PAGE2], EXTRACT_PAGE2, DEFAULT_DESCRIPTOR,
        {'name': [u'product 1'], 'image_url': [u'http://example.com/product1.jpg'],
            'description': [u'product 1 is great']}
    ),
    # can only work out correct placement by matching the second attribute first
    ('ambiguous description', [ANNOTATED_PAGE3], EXTRACT_PAGE3, DEFAULT_DESCRIPTOR,
        {'description': [u'description'], 'delivery': [u'delivery']}
    ),
    # infer a repeated structure
    ('repeated elements', [ANNOTATED_PAGE4], EXTRACT_PAGE4, DEFAULT_DESCRIPTOR,
        {'features': [u'feature1', u'feature2', u'feature3']}
    ),
    # identical variants with a repeated structure
    ('repeated identical variants', [ANNOTATED_PAGE5], EXTRACT_PAGE5, DEFAULT_DESCRIPTOR,
         {
             'description': [u'description'],
             'variants': [
                 {u'colour': [u'colour 1'], u'price': [u'price 1']},
                 {u'colour': [u'colour 2'], u'price': [u'price 2']},
                 {u'colour': [u'colour 3'], u'price': [u'price 3']}
             ]
         }
    ),
    ('variants with extra required attributes', [ANNOTATED_PAGE5a], EXTRACT_PAGE5, SAMPLE_DESCRIPTOR2,
         {
             'description': [u'description'],
             'variants': [
                 {u'colour': [u'colour 1'], u'price': [u'price 1']},
                 {u'colour': [u'colour 2'], u'price': [u'price 2']},
                 {u'colour': [u'colour 3'], u'price': [u'price 3']}
             ]
         }
    ),
    ('test that new descriptor is created from the original', [ANNOTATED_PAGE4], EXTRACT_PAGE4, SAMPLE_DESCRIPTOR2,
        {'features': [u'feature1', u'feature2', u'feature3']}
    ),
    # variants with an irregular structure
    ('irregular variants', [ANNOTATED_PAGE6], EXTRACT_PAGE6, DEFAULT_DESCRIPTOR,
         {
             'description': [u'description'],
             'variants': [
                 {u'name': [u'name 1']},
                 {u'name': [u'name 3']},
                 {u'name': [u'name 2']}
             ]
         }
    ),
    ('dont fail if extra required attribute has no field descriptor', [ANNOTATED_PAGE5a], EXTRACT_PAGE5,
        DEFAULT_DESCRIPTOR,
          {
             'description': [u'description'],
             'variants': [
                 {u'colour': [u'colour 1'], u'price': [u'price 1']},
                 {u'colour': [u'colour 2'], u'price': [u'price 2']},
                 {u'colour': [u'colour 3'], u'price': [u'price 3']}
             ]
         }
    ),

    # discovering repeated variants in table columns
#    ('variants in table columns', [ANNOTATED_PAGE7], EXTRACT_PAGE7, DEFAULT_DESCRIPTOR,
#         {'variants': [
#             {u'colour': [u'colour 1'], u'price': [u'price 1']},
#             {u'colour': [u'colour 2'], u'price': [u'price 2']},
#             {u'colour': [u'colour 3'], u'price': [u'price 3']}
#         ]}
#    ),


    # ignored regions
    (
    'ignored_regions', [ANNOTATED_PAGE8], EXTRACT_PAGE8, DEFAULT_DESCRIPTOR,
          {
             'description': [u'\n A very nice product for all intelligent people \n \n'],
             'price': [u'\n12.00\n(VAT exc.)'],
          }
    ),
    # ignored regions and text content extraction
    (
    'ignored_regions', [ANNOTATED_PAGE8], EXTRACT_PAGE8, SAMPLE_DESCRIPTOR4,
          {
             'description': [u'\n A very nice product for all intelligent people \n \n'],
             'price': [u'\n12.00\n(VAT exc.)'],
          }
    ),
    # shifted ignored regions (detected by region similarity)
    (
    'shifted_ignored_regions', [ANNOTATED_PAGE9], EXTRACT_PAGE9, DEFAULT_DESCRIPTOR,
          {
             'description': [u'\n A very nice product for all intelligent people \n \n'],
             'price': [u'\n12.00\n(VAT exc.)'],
          }
    ),
    (# special case with partial annotations
    'special_partial_annotation', [ANNOTATED_PAGE11], EXTRACT_PAGE11, DEFAULT_DESCRIPTOR,
          {
            'name': [u'SL342'],
            'description': ['\nSL342\n \nNice product for ladies\n \n&pound;85.00\n'],
            'price': [u'\xa385.00'],
            'price_before_discount': [u'\xa3100.00'],
          }
    ),
    (# with ignore-beneath feature
    'ignore-beneath', [ANNOTATED_PAGE12], EXTRACT_PAGE12a, DEFAULT_DESCRIPTOR,
          {
            'description': [u'\n A very nice product for all intelligent people \n'],
          }
    ),
    (# ignore-beneath with extra tags
    'ignore-beneath with extra tags', [ANNOTATED_PAGE12], EXTRACT_PAGE12b, DEFAULT_DESCRIPTOR,
          {
            'description': [u'\n A very nice product for all intelligent people \n'],
          }
    ),
    ('nested annotation with replica outside', [ANNOTATED_PAGE13a], EXTRACT_PAGE13a, DEFAULT_DESCRIPTOR,
          {'description': [u'\n A product \n $50.00 \nThis product is excelent. Buy it!\n \n'],
           'price': ["$50.00"],
           'name': [u'A product']}
    ),
    ('outside annotation with nested replica', [ANNOTATED_PAGE13b], EXTRACT_PAGE13b, DEFAULT_DESCRIPTOR,
          {'description': [u'\n A product \n $50.00 \nThis product is excelent. Buy it!\n'],
           'price': ["$45.00"],
           'name': [u'A product']}
    ),
    ('consistency check', [ANNOTATED_PAGE14], EXTRACT_PAGE14, DEFAULT_DESCRIPTOR,
          None,
    ),
    ('consecutive nesting', [ANNOTATED_PAGE15], EXTRACT_PAGE15, DEFAULT_DESCRIPTOR,
          {'description': [u'Description\n \n'],
           'price': [u'80.00']},
    ),
    ('nested inside not found', [ANNOTATED_PAGE16], EXTRACT_PAGE16, DEFAULT_DESCRIPTOR,
          {'price': [u'90.00'],
           'name': [u'product name']},
    ),
    ('ignored region helps to find attributes', [ANNOTATED_PAGE17], EXTRACT_PAGE17, DEFAULT_DESCRIPTOR,
          {'description': [u'\nThis product is excelent. Buy it!\n']},
    ),
    ('ignored region in partial annotation', [ANNOTATED_PAGE18], EXTRACT_PAGE18, DEFAULT_DESCRIPTOR,
          {u'site_id': [u'Item Id'],
           u'description': [u'\nDescription\n']},
    ),
    ('extra required attribute product', [ANNOTATED_PAGE19], EXTRACT_PAGE19a,
         SAMPLE_DESCRIPTOR1,
         {u'price': [u'60.00'],
          u'description': [u'description'],
          u'image_urls': [['http://example.com/image.jpg']],
          u'name': [u'Product name']},
    ),
    ('extra required attribute no product', [ANNOTATED_PAGE19], EXTRACT_PAGE19b,
         SAMPLE_DESCRIPTOR1,
         None,
    ),
    ('repeated partial annotations with variants', [ANNOTATED_PAGE20], EXTRACT_PAGE20, DEFAULT_DESCRIPTOR,
            {u'variants': [
                {'price': ['270'], 'name': ['Twin']},
                {'price': ['330'], 'name': ['Queen']},
            ]},
    ),
    ('variants with swatches', [ANNOTATED_PAGE21], EXTRACT_PAGE21, DEFAULT_DESCRIPTOR,
            {u'category': [u'chairs'],
             u'image_urls': [u'image.jpg'],
             u'variants': [
                {'swatches': ['swatch1.jpg']},
                {'swatches': ['swatch2.jpg']},
                {'swatches': ['swatch3.jpg']},
                {'swatches': ['swatch4.jpg']},
             ]
            },
    ),
    ('variants with swatches complete', [ANNOTATED_PAGE22], EXTRACT_PAGE22, DEFAULT_DESCRIPTOR,
            {u'category': [u'chairs'],
             u'variants': [
                 {u'swatches': [u'swatch1.jpg'],
                  u'price': [u'$70'],
                  u'name': [u'product 1']},
                 {u'swatches': [u'swatch2.jpg'],\
                  u'price': [u'$80'],
                  u'name': [u'product 2']},
                 {u'swatches': [u'swatch3.jpg'],
                  u'price': [u'$90'],
                  u'name': [u'product 3']},
                 {u'swatches': [u'swatch4.jpg'],
                  u'price': [u'$100'],
                  u'name': [u'product 4']}
             ],
             u'image_urls': [u'image.jpg']},
    ),
    ('repeated (variants) with ignore annotations', [ANNOTATED_PAGE23], EXTRACT_PAGE23, DEFAULT_DESCRIPTOR,
        {'variants': [
            {u'price': [u'300'], u'name': [u'Variant 1']},
            {u'price': [u'320'], u'name': [u'Variant 2']},
            {u'price': [u'340'], u'name': [u'Variant 3']}
            ]},
    ),
    (# dont fail when there are two consecutive ignore-beneath
    'double ignore-beneath inside annotation', [ANNOTATED_PAGE24], EXTRACT_PAGE24, DEFAULT_DESCRIPTOR,
          {
            'description': [u'\n A very nice product for all intelligent people \n'],
          }
    ),
    ('repeated partial annotation within same tag', [ANNOTATED_PAGE25], EXTRACT_PAGE25, DEFAULT_DESCRIPTOR,
            {"name": ['"Large"', '"X Large"', '"XX Large"']}
    ),
    ('repeated partial annotation within same tag, variants version', [ANNOTATED_PAGE26], EXTRACT_PAGE26, DEFAULT_DESCRIPTOR,
            {"variants": [
                {"name": ['"Large"']},
                {"name": ['"X Large"']},
                {"name": ['"XX Large"']}
            ]}
    ),
    ('repeated partial annotation within same tag, variants version with more than one attribute',
            [ANNOTATED_PAGE27], EXTRACT_PAGE27, DEFAULT_DESCRIPTOR,
            {"variants": [
                {"name": ['"Large"'], "site_id": ["44"]},
                {"name": ['"X Large"'], "site_id": ["45"]},
                {"name": ['"XX Large"'], "site_id": ["46"]}
            ]}
    ),
    ('repeated partial annotation within same tag, variants version with more than one attribute, more annotations around',
            [ANNOTATED_PAGE28], EXTRACT_PAGE28, DEFAULT_DESCRIPTOR, {
                "price": ["Price: 45"],
                "variants": [
                    {"name": ['"Large"'], "site_id": ["44"]},
                    {"name": ['"X Large"'], "site_id": ["45"]},
                    {"name": ['"XX Large"'], "site_id": ["46"]}]
            }
    ),
    ('repeated annotation inside variants', [ANNOTATED_PAGE29], EXTRACT_PAGE29, DEFAULT_DESCRIPTOR,
            {'variants': [
                {u'tag': [u'Tag 1', u'Tag 2', u'Tag 3'], u'description': [u'Desc 1'], u'name': [u'Name 1']},
                {u'tag': [u'Tag 4', u'Tag 5', u'Tag 6'], u'description': [u'Desc 2'], u'name': [u'Name 2']},
                {u'tag': [u'Tag 7', u'Tag 8', u'Tag 9'], u'description': [u'Desc 3'], u'name': [u'Name 3']}]
            }

    ),
    ('avoid false positives by allowing to extract only from text content', [ANNOTATED_PAGE30], EXTRACT_PAGE30a, SAMPLE_DESCRIPTOR3,
        None
    ),
    ('only extract from text content', [ANNOTATED_PAGE30], EXTRACT_PAGE30b, SAMPLE_DESCRIPTOR3,
        {u'phone': [u'029847272']}
    ),
    ('avoid false positives on comments', [ANNOTATED_PAGE30], EXTRACT_PAGE30c, SAMPLE_DESCRIPTOR3,
        None
    ),
    ('avoid false positives on scripts', [ANNOTATED_PAGE30], EXTRACT_PAGE30d, SAMPLE_DESCRIPTOR3,
        None
    ),
    ('correctly extract regions that follows more than one consecutive misses', [ANNOTATED_PAGE31], EXTRACT_PAGE31, SAMPLE_DESCRIPTOR1a,
        {
            u'price': [u'60.00'],
            u'name': [u'Product name'],
            u'image_urls': [['http://example.com/image.jpg']]
        }
    ),
    ('single ignored region inside a repeated structure', [ANNOTATED_PAGE32], EXTRACT_PAGE32, DEFAULT_DESCRIPTOR,
        {'features': [u'feature1', u'feature2', u'feature3']}
    ),
]

class Page33Extractor(RecordExtractor):
    def __init__(self, extractors, template):
        RecordExtractor.__init__(self, extractors, template)
        self.best_match = first_longest_subsequence

class Page33IBLExtractor(InstanceBasedLearningExtractor):
    def build_extraction_tree(self, template, type_descriptor, trace=True):
        attribute_map = type_descriptor.attribute_map if type_descriptor else None
        extractors = BasicTypeExtractor.create(template.annotations, attribute_map)
        if trace:
            extractors = TraceExtractor.apply(template, extractors)
        for cls in (Page33Extractor,):
            extractors = cls.apply(template, extractors)
            if trace:
                extractors = TraceExtractor.apply(template, extractors)

        return TemplatePageExtractor(template, extractors)

# test bundles with different IBL extractor tree
TEST_IBL_DATA = [
    ('match with class attributes', Page33IBLExtractor, [ANNOTATED_PAGE33], EXTRACT_PAGE33, SAMPLE_DESCRIPTOR33,
        {
             u'date': [u'10/10/2011'],
             u'text': [u'review goes here. test..'],
             u'author': [u'Jennifer M.']
        }
    ),
    ('1131/cgarsltd.co.uk pages 1', InstanceBasedLearningExtractor, [ANNOTATED_PAGE34], EXTRACT_PAGE34A, PAGE34_DESCRIPTOR,
        {
             u"1_description": [
                 u"10 year old cask strength whisky slightly smoky, spicy and with a rich, long-lasting finish"
             ],
             u"1_image": [
                 ["images/thumbs/380x380_Glenfarclas105_35cl.JPG"]
             ],
             u"1_name": [
                 u"Glenfarclas 105 - 35cl 60%"
             ],
             u"1_price": [
                 u"31.99"
             ]
        }
    ),
    ('1131/cgarsltd.co.uk pages 2', InstanceBasedLearningExtractor, [ANNOTATED_PAGE34], EXTRACT_PAGE34B, PAGE34_DESCRIPTOR,
        {
             u"1_description": [
                 "Packaging Pack of 5 Petit Corona size Ring Gauge 30 Length 5\" Tasting Notes Hand Rolled in the Dominican Republic. individually cello wrapped cigars. All of the flavours are made from natural ingredients. Long filler, and binder tobacco from Dominica. Indonesian Sumatra wrapper."
             ],
             u"1_image": [
                 ["images/thumbs/380x475_Flavoured5pack_RUM_1.jpg"]
             ],
             u"1_name": [
                 "Heaven Petit Corona Raging Rum Cigar - 5 Pack"
             ],
             u"1_price": [
                 "30.49"
             ]
        }
    ),
    ('873/seedevolution pages 1', InstanceBasedLearningExtractor, [ANNOTATED_PAGE35], EXTRACT_PAGE35A, PAGE35_DESCRIPTOR,
        {
             u"bild": [
            ["http://www.meinwoody.de/media/catalog/product/cache/1/image/800x800/9df78eab33525d08d6e5fb8d27136e95/t/o/topf_banderole_600x600px_wildbirne2.jpg"]
        ],
             u"titel": [
                 "Pflanzset Wildbirne Baum"
             ],
             u"beschreibung": [
                 u"Wildbirne: Als eine wirkliche Seltenheit, ja fast schon als Sensation ist die Wildbirne eine traumhafter Anblick. Sie erreicht meist eine Höhe von bis zu 20 Metern und vereint mit seiner saftigen Frucht hervorragende Eigenschaften in sich. Die Wildbirne hat einen festfleischigen, säuerlich-süßes Aroma und ist als Kompott ein echter Klassiker. Der Wildbirnenbaum wird im Sommer von einer weißen Blütenpracht geschmückt. Das Holz der Wildbirne ist sehr begehrt, da die Bestände sehr gering und die Preise hoch sind. In manche Regionen gilt der Wildbirnenbaum als gefährdete Art. Dabei ermöglicht er zahlreichen Tierarten das Leben und Überleben in freier Wildbahn. Wildbirne als Heilmittel Wildbirne: Die Frucht der Wildbirne gilt als Heilmittel bei Durchfall, Migräne und Pleuritis. Die Blüten des Wildbirnenbaums werden häufig als Tee bei Nierenbeckenentzündung eingesetzt. Der Birnensaft dient ebenfalls als Kur zur Entgiftung des Körpers. Jetzt Wildbirne Baum Pflanzset kaufen"
             ],
             u"rabattpreis": [
                 "100"
             ],
             u"preis": [
                 "2013"
             ],
        }
    ),
    ('302/chasexy pages 1', InstanceBasedLearningExtractor, [ANNOTATED_PAGE37], EXTRACT_PAGE37A, PAGE37_DESCRIPTOR,
        {
            u"Imagem": [
                ["http://www.chasexy.com.br/media/catalog/product/cache/1/image/265x265/05a6ecf64b09a2402cf2b444174c1c75/s/e/separador_pernas_chasexy_01.jpg"]
            ],
            u"Nome": [
                u"Separador de Pernas com bastão e algemas em couro sintético - Chá Sexy Shop"
            ],
            u"Preco": [
                "45.00"
            ],
        }
    ),
]

class TestExtraction(TestCase):
    @parameterized.expand(TEST_DATA)
    def test_extraction(self, name, templates, page, descriptor, expected_output):
        template_pages = [HtmlPage(None, {}, t) for t in templates]

        extractor = InstanceBasedLearningExtractor([(t, descriptor) for t in template_pages])
        actual_output, _ = extractor.extract(HtmlPage(None, {}, page))
        self.assertEqual(expected_output, actual_output and actual_output[0])

    @parameterized.expand(TEST_IBL_DATA)
    def test_ibl(self, name, ibl_class, templates, page, descriptor, expected_output):
        template_pages = [HtmlPage(None, {}, t) for t in templates]

        extractor = ibl_class([(t, descriptor) for t in template_pages])
        actual_output, _ = extractor.extract(HtmlPage(None, {}, page))
        extracted = actual_output and actual_output[0]
        expected_keys = sorted(expected_output.keys())
        extracted_keys = sorted(extracted.keys())

        self.assertEqual(expected_keys, extracted_keys)
        for k in expected_keys:
            self.assertEqual(expected_output[k], extracted[k])
