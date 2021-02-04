__author__ = 'Robbert Harms'
__date__ = '2021-01-28'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
import shutil
import zipfile

from dataclasses import dataclass

import pypandoc
from bs4 import BeautifulSoup


class TextData:

    def __init__(self, text):
        """Representation of textual information.

        Args:
            text: the string with the text
        """
        self.text = text

    def is_plaintext(self):
        """Check if this node contains only plaintext data.

        Returns:
            bool: If this node contains text without markup, i.e. plain text
        """
        raise NotImplementedError()

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

    def to_markdown(self):
        """Convert the text in this node to Markdown and return that.

        Returns:
            str: a Markdown conversion of the text in this node
        """
        raise NotImplementedError()

    def to_plaintext(self):
        """Convert the text in this node to plain text.

        Returns:
            str: the text in this node as plain text
        """
        raise NotImplementedError()

    def get_resources(self):
        """Get a list of :class:`YbeResources` from this data.

        Returns:
            List[YbeResource]: list of resources data.
        """
        raise NotImplementedError()

    def __str__(self):
        return self.text

    def __repr__(self):
        return f'{self.__class__.__name__}(text={repr(self.text)})'


class TextPlain(TextData):

    def is_plaintext(self):
        return True

    def to_html(self):
        return self.text

    def to_latex(self):
        return self.text

    def to_markdown(self):
        return self.text

    def to_plaintext(self):
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

    def is_plaintext(self):
        return False

    def to_html(self):
        return self.text

    def to_latex(self):
        return pypandoc.convert_text(self.text, 'latex', 'html')

    def to_markdown(self):
        return pypandoc.convert_text(self.text, 'md', 'html')

    def to_plaintext(self):
        parsed = BeautifulSoup(self.text, 'lxml')
        return parsed.get_text()

    def get_resources(self):
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

    def is_plaintext(self):
        return False

    def to_html(self):
        return pypandoc.convert_text(self.text, 'html', 'md', extra_args=['--mathjax'])

    def to_latex(self):
        return pypandoc.convert_text(self.text, 'latex', 'md')

    def to_markdown(self):
        return self.text

    def to_plaintext(self):
        return self.text

    def get_resources(self):
        return TextHTML(self.to_html()).get_resources()


@dataclass
class ResourceData:
    """Reference to a file for included content."""
    path: str = None


@dataclass
class ImageResource(ResourceData):
    """Path and meta data of an image which need to be included as a resource."""
    alt: str = None


@dataclass
class YbeResourceContext:
    """The context used to load Ybe resource."""

    def copy_resource(self, resource, dirname):
        """Copy the indicated resource to the indicated directory.

        Args:
            resource (ResourceData): the resource to copy
            dirname (str): the directory to copy to

        Returns:
            str: the path to the new file
        """
        raise NotImplementedError()


@dataclass
class ZipArchiveContext(YbeResourceContext):
    """Loading resources from a zipped archive."""
    path: str

    def copy_resource(self, resource, dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if os.path.isabs(resource.path):
            return shutil.copy(resource.path, dirname)
        else:
            if subdir := os.path.dirname(resource.path):
                dirname = os.path.join(dirname, subdir) + '/'

                if not os.path.exists(dirname):
                    os.makedirs(dirname)

            archive = zipfile.ZipFile(self.path, 'r')
            return archive.extract(resource.path, dirname)


@dataclass
class DirectoryContext(YbeResourceContext):
    """Loading resources from a directory"""
    path: str

    def copy_resource(self, resource, dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if os.path.isabs(resource.path):
            return shutil.copy(resource.path, dirname)
        else:
            if subdir := os.path.dirname(resource.path):
                dirname = os.path.join(dirname, subdir) + '/'

                if not os.path.exists(dirname):
                    os.makedirs(dirname)

            return shutil.copy(os.path.join(self.path, resource.path), dirname)
