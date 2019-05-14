import numpy as np

from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    InputMultiPath, OutputMultiPath, File, Directory,
    traits, isdefined
    )
from nipype.utils.filemanip import split_filename
import nibabel as nb
from nilearn.input_data import NiftiLabelsMasker
from nilearn.connectome import ConnectivityMeasure
from fmridenoise.utils.quality_measures import create_carpetplot
from nilearn.plotting import plot_matrix

class ConnectivityInputSpec(BaseInterfaceInputSpec):
    fmri_denoised = File(exists=True,
                         desc='Denoised fMRI file',
                         mandatory=True)
    parcellation = File(exists=True,
                        desc='Parcellation file',
                        mandatory=True)
    output_dir = File(desc='Output path')


class ConnectivityOutputSpec(TraitedSpec):
    corr_mat = File(exists=True,
                    desc='Connectivity matrix',
                    mandatory=True)
    carpet_plot = File(exists=True,
                    desc='Carpet plot',
                    mandatory=True)
    matrix_plot = File(exists=True,
                    desc='Carpet plot',
                    mandatory=True)


class Connectivity(SimpleInterface):
    input_spec = ConnectivityInputSpec
    output_spec = ConnectivityOutputSpec

    def _run_interface(self, runtime):
        fname = self.inputs.fmri_denoised
        bold_img = nb.load(fname)
        masker = NiftiLabelsMasker(labels_img=self.inputs.parcellation, standardize=True)
        time_series = masker.fit_transform(bold_img, confounds=None)

        corr_measure = ConnectivityMeasure(kind='correlation')
        corr_mat = corr_measure.fit_transform([time_series])[0]
        _, base, _ = split_filename(fname)

        conn_file = f'{self.inputs.output_dir}/{base}_conn_mat.npy'

        carpet_plot_file = f'{self.inputs.output_dir}/{base}_carpet_plot.png'
        matrix_plot_file = f'{self.inputs.output_dir}/{base}_matrix_plot.png'

        create_carpetplot(time_series, carpet_plot_file)
        mplot = plot_matrix(corr_mat)
        mplot.figure.savefig(matrix_plot_file)

        np.save(conn_file, corr_mat)

        self._results['corr_mat'] = conn_file
        self._results['carpet_plot'] = carpet_plot_file
        self._results['matrix_plot'] = matrix_plot_file

        return runtime


# --- TESTS

if __name__ == '__main__':

    conn = Connectivity()
    conn.inputs.fmri_denoised = '/media/finc/Elements/fmridenoise/derivatives/fmridenoise/sub-01_task-rhymejudgment_space-MNI152NLin2009cAsym_desc-preproc_bold_denoised.nii'
    conn.inputs.parcellation = '/home/finc/Dropbox/Projects/fMRIDenoise/fmridenoise/fmridenoise/parcellation/Schaefer2018_200Parcels_7Networks_order_FSLMNI152_1mm.nii.gz'
    conn.inputs.output_dir = '/media/finc/Elements/fmridenoise/derivatives/fmridenoise/'
    results = conn.run()

    print(results.outputs)