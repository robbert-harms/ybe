__author__ = 'Robbert Harms'
__date__ = '2021-01-28'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


import pypandoc
from bs4 import BeautifulSoup
from ybe.lib.utils import markdown_to_latex, html_to_latex


class TextData:

    def __init__(self, text):
        """Representation of textual information.

        Args:
            text: the string with the text
        """
        self.text = text

    def to_html(self):
        """Convert the text in this node to HTML and return that.

        Returns:
            str: a HTML conversion of this text block node
        """
        raise NotImplementedError()

    def to_latex(self):
        """Convert the text in this node to Latex and return that.

        Returns:
            str: a Latex conversion of the text in this node
        """
        raise NotImplementedError()

    def get_resources(self):
        """Get a list of :class:`YbeResources` in this node or sub-tree.

        This will need to do a recursive lookup to find all the resources.

        Returns:
            List[YbeResource]: list of resources nodes.
        """
        raise NotImplementedError()

    def __str__(self):
        return self.text

    def __repr__(self):
        return f'{self.__class__.__name__}(text={self.text})'


class TextNoMarkup(TextData):

    def to_html(self):
        return self.text

    def to_latex(self):
        return self.text

    def get_resources(self):
        return []


class TextHTML(TextData):
    yaml_tag = u'!html'

    @classmethod
    def to_yaml(cls, representer, node):
        style = None
        if '\n' in node.text:
            style = '|'
        return representer.represent_scalar(cls.yaml_tag, node.text, style=style)

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls(node.value)

    def to_html(self):
        return self.text

    def to_latex(self):
        return html_to_latex(self.text)

    def get_resources(self):
        from ybe.lib.ybe_nodes import ImageResource

        parsed = BeautifulSoup(self.text, 'lxml')

        def only_files(src):
            return not any(src.startswith(el) for el in ['http://', 'https://', 'data:'])

        resources = []
        for img in parsed.find_all('img', src=only_files):
            resources.append(ImageResource(path=img.get('src'), alt=img.get('alt')))
        return resources


class TextMarkdown(TextData):
    yaml_tag = u'!markdown'

    @classmethod
    def to_yaml(cls, representer, node):
        style = None
        if '\n' in node.text:
            style = '|'
        return representer.represent_scalar(cls.yaml_tag, node.text, style=style)

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls(node.value)

    def to_html(self):
        return pypandoc.convert_text(self.text, 'html', 'md', extra_args=['--mathjax'])

    def to_latex(self):
        return markdown_to_latex(self.text)

    def get_resources(self):
        return TextHTML(self.to_html()).get_resources()
