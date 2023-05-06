import datetime
import json
import os


class FilenamesCollector:
    def __init__(self):
        self.base_directory = os.path.abspath(os.path.join(os.path.join(__file__, os.pardir), os.pardir))
        self.seq_data_directory = os.path.join(self.base_directory, 'seq_data/')
        self.reference_dir = os.path.join(self.seq_data_directory, 'reference/hg38')

    def get_reference_filename(self) -> str:
        self._check_if_exists(self.reference_dir)
        return [
            self._check_if_unzipped(file) for file in os.listdir(self.reference_dir) if file.endswith('fasta') or file.endswith('fna')
        ][0]

    def get_path_to_project(self) -> str:
        with open(os.path.join(self.seq_data_directory, 'location.txt'), 'r') as location_file:
            location_path = location_file.read().rstrip('\n')
        return f'{location_path}/seq_data'

    def get_annotation_bed(self) -> str:
        self._check_if_exists(self.reference_dir)
        return [
            self._check_if_unzipped(file) for file in os.listdir(self.reference_dir) if file.endswith('bed')
        ][0]

    def get_annotation_gtf(self) -> str:
        self._check_if_exists(self.reference_dir)
        return [
            self._check_if_unzipped(file) for file in os.listdir(self.reference_dir) if file.endswith('gtf')
        ][0]

    def get_fastqs(self) -> tuple:
        fastqs_data_dir = os.path.join(self.seq_data_directory, 'reads/')
        self._check_if_exists(fastqs_data_dir)
        files = [self._check_if_unzipped(file) for file in os.listdir(fastqs_data_dir)]
        if len(files) != 2:
            raise Exception('Please, provide only uncompressed paired reads!')
        return files[0], files[1]

    def get_base_filename(self) -> str:
        return f'{datetime.datetime.now().strftime("%d%m%Y_%H%M%S")}_{self.get_fastqs()[0].split(".")[0]}'

    @staticmethod
    def _check_if_exists(path_to: str) -> None:
        if not (os.listdir(path_to) or os.path.exists(path_to)):
            raise FileNotFoundError(f'{path_to} not found, please provide!')

    @staticmethod
    def _check_if_unzipped(filename: str) -> str:
        if filename.endswith('gz'):
            raise EncodingWarning(f'Please, provide only uncompressed, not {filename}!')
        return filename


class ParametersCollector:

    @staticmethod
    def parse_parameters_json() -> dict:
        with open(os.path.join(
            FilenamesCollector().seq_data_directory, 'dag_parameters.json'
        ), "r") as f:
            data = json.load(f)
        return data


if __name__ == '__main__':
    print(FilenamesCollector().get_base_filename())

