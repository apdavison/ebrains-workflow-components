# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack.package import *


class PyFmriprep(PythonPackage):
    # Project description
    """fMRIPrep is a functional magnetic resonance imaging (fMRI) data preprocessing pipeline that is designed to provide an easily accessible, state-of-the-art interface that is robust to variations in scan acquisition protocols and that requires minimal user input, while providing easily interpretable and comprehensive error and output reporting."""

    # FMRIPrep home page.
    homepage = "https://fmriprep.org/en/stable/"
    url      = "https://github.com/nipreps/fmriprep/archive/refs/tags/24.0.0.tar.gz"
    pypi     = "fmriprep/fmriprep-24.0.0.tar.gz"

    # FIXME: Add a list of maintainers
    # maintainers = ['']

    # FMRIPrep last release
    version('24.0.0', sha256='387a9b16f721aafc9e4ae77fb3328741b844afd9dec4297fabec6f0faa5ea89e')

    # Dependencies.
    depends_on('python@3.8:', type=('build', 'run'))
    depends_on('py-nipype', type=('build', 'run'))
    depends_on('fsl', type=('build', 'run')) # FSL (version 6.0.7.7)
    depends_on('ants@2.5.1', type=('build', 'run')) # ANTs (version 2.5.1)
    # depends_on('afni', type=('build', 'run')) # AFNI (version 24.0.05)
    depends_on('c3d', type=('build', 'run')) # C3D (version 1.4.0)
    depends_on('freesurfer@7.3.2', type=('build', 'run')) # FreeSurfer (version 7.3.2)
    depends_on('py-bids-validator', type=('build', 'run')) # bids-validator (version 1.14.0)
    # depends_on('connectome-workbench', type=('build', 'run')) # connectome-workbench (version 1.5.0)