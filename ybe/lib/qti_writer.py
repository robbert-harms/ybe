__author__ = 'Robbert Harms'
__date__ = '2020-04-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
import shutil
import tempfile
import uuid
import importlib.resources as pkg_resources
from hashlib import md5


def write_qti_zip(ybe_file, fname):
    """Write the provided Ybe object as a QTI zip.

    Args:
        ybe_file (ybe.lib.ybe_file.YbeFile): the ybe file object to dump
        fname (str): the filename to dump to
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        write_qti_dir(ybe_file, tmp_dir)
        shutil.make_archive(fname.rstrip('.zip'), 'zip', tmp_dir)


def write_qti_dir(ybe_file, dirname):
    """Write the provided Ybe object as a QTI zip.

    Args:
        ybe_file (ybe.lib.ybe_file.YbeFile): the ybe file object to dump
        dirname (str): the directory to write to
    """
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    assessment_identifier = md5(str(ybe_file).encode('utf-8')).hexdigest()
    dependency_identifier = uuid.uuid4().hex

    if not os.path.exists(d := os.path.join(dirname, assessment_identifier)):
        os.makedirs(d)

    _write_assessment_meta(ybe_file, dirname, assessment_identifier)
    resources = _write_questions_data(ybe_file, dirname, assessment_identifier, dependency_identifier)
    _write_qti_manifest(ybe_file, dirname, assessment_identifier, dependency_identifier, resources)

    # with open(os.path.join(dirname, 'imsmanifest.xml'), 'w') as f:


def _write_assessment_meta(ybe_file, dirname, assessment_identifier):
    """Write the QTI data manifest.

        Args:
            ybe_file (ybe.lib.ybe_contents.YbeFile): the ybe file object to dump
            dirname (str): the directory to write the manifest (``imsmanifest.xml``) to.
            assessment_identifier (str): UUID of the assessment
            dependency_identifier (str): UUID of the dependencies
        """
    template_items = {
        'title': ybe_file.info.title,
        'description': ybe_file.description,
        # 'points_possible': ybe_file
        'assignment_identifier': uuid.uuid4().hex,
        'assessment_identifier': assessment_identifier,
        'assignment_group_identifier': uuid.uuid4().hex
    }
    template = pkg_resources.read_text('ybe.data.qti_templates', 'assessment_meta.xml')
    manifest_str = template.format(**template_items)


def _write_questions_data(ybe_file, dirname, assessment_identifier, dependency_identifier):
    # todo: write the questions data, copy the resources and create new resource identifiers mapping to the relative paths

    return []


def _write_qti_manifest(ybe_file, dirname, assessment_identifier, dependency_identifier, resources):
    """Write the QTI data manifest.

    Args:
        ybe_file (ybe.lib.ybe_contents.YbeFile): the ybe file object to dump
        dirname (str): the directory to write the manifest (``imsmanifest.xml``) to.
        assessment_identifier (str): UUID of the assessment
        dependency_identifier (str): UUID of the dependencies
    """
    template_items = {
        'manifest_identifier': uuid.uuid4().hex,
        'title': ybe_file.info.title,
        'date': ybe_file.info.creation_date,
        'assessment_identifier': assessment_identifier,
        'dependency_identifier': dependency_identifier
    }
    template = pkg_resources.read_text('ybe.data.qti_templates', 'imsmanifest.xml')
    manifest_str = template.format(**template_items)

    # todo enter the resources into the manifest

    with open(os.path.join(dirname, 'imsmanifest.xml'), 'w') as f:
        f.write(manifest_str)

