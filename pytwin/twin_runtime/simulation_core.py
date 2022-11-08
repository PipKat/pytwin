import os
import json
import sys
import time
import platform
import numpy as np
from enum import Enum
from pathlib import Path
from ctypes import cdll, POINTER, c_char_p, c_double, c_void_p, c_bool, byref, c_size_t
from typing import List, Dict, Tuple, Union, Set

if platform.system() == 'Windows':
    import win32api

from .constants import *

if platform.system() == 'Windows':
    OS_VERSION = 'win64'
else:
    OS_VERSION = 'linux64'

CUR_DIR = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
os.environ['TWIN_RUNTIME_SDK'] = str(Path(CUR_DIR) / OS_VERSION)
os.environ['SIMULATION_MANAGER_DIR'] = str(Path(CUR_DIR) / OS_VERSION)
default_log_name = "model.log"
os.environ['LD_LIBRARY_PATH'] = str(Path(CUR_DIR) / OS_VERSION)

EMPTY_STRING_C = c_char_p(''.encode())
TIME_LABEL_C = c_char_p(b'Time')

class VisualizationTypes(Enum):
    IMAGE = 0
    BIN = 1


class ROMState:
    vis_type: str = None
    enable: bool = None
    views: List[str] = None

    def __init__(self, vis_type, enable, views=None):
        self.vis_type = vis_type
        self.enable = enable
        self.views = views


class TwinStatus(Enum):
    TWIN_STATUS_OK = 0
    TWIN_STATUS_WARNING = 1
    TWIN_STATUS_ERROR = 2
    TWIN_STATUS_FATAL = 3


class SchematicMetadata:
    number_of_comopnents: int
    cloud_input_number: int
    cloud_input_names_c: Tuple[c_char_p]
    cloud_input_names: Set[str]

class SimulationCore:

    debug_mode = False

    os_version = None

    if platform.system() == 'Windows':
        simulation_core_library = 'SimulationCore.dll'
        os_version = 'win64'
    else:
        simulation_core_library = 'libSimulationCore.so'
        os_version = 'linux64'

    @staticmethod    
    def load_dll(library_path=None):

        def _setup_env(sdk_folder_path):
            if platform.system() == 'Windows':
                sep = ';'
            else:
                sep = ':'
            if sdk_folder_path not in os.environ['PATH']: 
                os.environ['PATH'] = '{}{}{}'.format(sdk_folder_path, sep, os.environ['PATH'])

        if library_path is None:
            folder = os.path.join(CUR_DIR, SimulationCore.os_version)
            _setup_env(sdk_folder_path=folder)
            return cdll.LoadLibrary(os.path.join(folder, SimulationCore.simulation_core_library))

        else:
            _setup_env(sdk_folder_path=os.path.dirname(library_path))
            return cdll.LoadLibrary(library_path)

    @staticmethod
    def make_resp(success: bool, code: int, description: str, data: Dict = None, error: Dict = None):
        resp = {'description': description,
                'success': success,
                'code': code,
                }
        if data:
            resp['data'] = data
        if error:
            resp['error'] = error
        return resp

    def __init__(self):
        self._simulation_library = SimulationCore.load_dll()

        self._LoadJsonSchematic = self._simulation_library.LoadJsonSchematic
        self._LoadJsonSchematic.restype = c_size_t

        self._CloseJsonSchematic = self._simulation_library.CloseJsonSchematic
        self._CloseJsonSchematic.restype = c_void_p

        self._LoadModels = self._simulation_library.LoadModels
        self._LoadModels.restype = c_void_p

        self._CloseModels = self._simulation_library.CloseModels
        self._CloseModels.restype = c_void_p

        self._GetNumberOfNodes = self._simulation_library.GetNumberOfNodes
        self._GetNumberOfNodes.restype = c_size_t

        self._GetRomResourceDirectory = self._simulation_library.GetRomResourceDirectory
        self._GetRomResourceDirectory.restype = c_char_p

        self._SetRomVisualizationDirectory = self._simulation_library.SetRomVisualizationDirectory

        self._Enable3DRomImageGeneration = self._simulation_library.Enable3DRomImageGeneration
        self._Enable3DRomImageGeneration.restype = c_void_p

        self._Disable3DRomImageGeneration = self._simulation_library.Disable3DRomImageGeneration
        self._Disable3DRomImageGeneration.restype = c_void_p

        self._EnableRomImageGeneration = self._simulation_library.EnableRomImageGeneration
        self._EnableRomImageGeneration.restype = c_void_p

        self._DisableRomImageGeneration = self._simulation_library.DisableRomImageGeneration
        self._DisableRomImageGeneration.restype = c_void_p

        self._GetNumRomImageFiles = self._simulation_library.GetNumRomImageFiles
        self._GetNumRomImageFiles.restype = c_void_p

        self._GetRomImageFiles = self._simulation_library.GetRomImageFiles
        self._GetRomImageFiles.restype = c_void_p

        self._GetNumRomModeCoefFiles = self._simulation_library.GetNumRomModeCoefFiles
        self._GetNumRomModeCoefFiles.restype = c_void_p

        self._GetRomModeCoefFiles = self._simulation_library.GetRomModeCoefFiles
        self._GetRomModeCoefFiles.restype = c_void_p

        self._GetNumRomSnapshotFiles = self._simulation_library.GetNumRomSnapshotFiles
        self._GetNumRomSnapshotFiles.restype = c_void_p

        self._GetRomSnapshotFiles = self._simulation_library.GetRomSnapshotFiles
        self._GetRomSnapshotFiles.restype = c_void_p

        self._UpdateSrcDataPack = self._simulation_library.UpdateSrcDataPack
        self._UpdateSrcDataPack.restype = c_size_t

        self._GetSrcNodeOutputNumber = self._simulation_library.GetSrcNodeOutputNumber
        self._GetSrcNodeOutputNumber.restype = c_size_t

        self._GetSrcNodeOutputNames = self._simulation_library.GetSrcNodeOutputNames

        self._SetParameters = self._simulation_library.SetParameters
        self._SetParameters.restype = c_void_p

        self._SetInputStartValues = self._simulation_library.SetInputStartValues
        self._SetInputStartValues.restype = c_void_p

        self._Simulate = self._simulation_library.Simulate
        self._Simulate.restype = c_void_p

        self._GetDataSize = self._simulation_library.GetDataSize
        self._GetDataSize.restype = c_size_t

        self._GetDataForSocket = self._simulation_library.GetDataForSocket
        self._GetDataForSocket.restype = c_void_p

        self._GetNodeOutputNumber = self._simulation_library.GetNodeOutputNumber
        self._GetNodeOutputNumber.argtypes = [c_char_p]
        self._GetNodeOutputNumber.restype = c_size_t

        self._GetNodeOutputs = self._simulation_library.GetNodeOutputs
        self._GetNodeOutputs.restype = c_void_p

        self._GetSimulationSummary = self._simulation_library.GetSimulationSummary
        self._GetSimulationSummary.restype = c_char_p

        self._ResetModels = self._simulation_library.ResetModels
        self._ResetModels.restype = c_void_p

        self._GetLogContents = self._simulation_library.GetLogContents
        self._GetLogContents.restype = c_char_p

        self._metadata: SchematicMetadata = None

    def _build_metadata(self):
        self._metadata = SchematicMetadata()
        self._metadata.cloud_input_number = self._GetSrcNodeOutputNumber()

        src_node_output_names_c = (c_char_p * self._metadata.cloud_input_number)()
        self._GetSrcNodeOutputNames(byref(src_node_output_names_c))

        self._metadata.cloud_input_names_c = src_node_output_names_c
        self._metadata.cloud_input_names = set([x.decode() for x in src_node_output_names_c])

    def _clean_metadata(self):
        if self._metadata:
            del self._metadata
            self._metadata = None

    def get_src_node_output_number(self):
        output_number = self._GetSrcNodeOutputNumber()
        return output_number

    def update_cloud_data(self, data: List[Dict], validate=False, dry_run=False):
        n_lines = len(data)
        all_labels = set()
        for label, value in data[0].items():
            if label.lower() != 'time':
                all_labels.add(label)

        n_cols = len(all_labels) + 1  # +1 for Time column

        if validate:
            datapoint_labels = set()
            for datapoint in data:
                datapoint_labels.clear()
                for label, value in datapoint.items():
                    if label.lower() == 'time':
                        continue
                    elif label not in self._metadata.cloud_input_names:
                        description = f'Datapoint names are not consistent. Extra label found: {label}.'
                        return SimulationCore.make_resp(success=False,
                                                        code=TD_UPDATE_SRCDATA_PCK_ERROR,
                                                        description=description)
                    if not (isinstance(value, int) or isinstance(value, float)):
                        description = f'Error parsing source data. Value of parameter {label} ' \
                                      f'can only be a number.'
                        return SimulationCore.make_resp(success=False,
                                                        code=TD_UPDATE_SRCDATA_PCK_ERROR,
                                                        description=description)
                    datapoint_labels.add(label)
                if datapoint_labels != self._metadata.cloud_input_names:
                    difference = ','.join(self._metadata.cloud_input_names - datapoint_labels)
                    description = f'Error parsing source data. Expected parameters {difference} do not exist in source data. ' \
                                  f'Please note that parsing is case sensitive.'
                    return SimulationCore.make_resp(success=False,
                                                    code=TD_UPDATE_SRCDATA_PCK_ERROR,
                                                    description=description)

        input_data = build_ctype_2d_array_from_records(n_lines, n_cols, data)

        errors = c_char_p()

        if not dry_run:
            self._UpdateSrcDataPack(c_size_t(n_lines), c_size_t(n_cols), self._metadata.cloud_input_names_c,
                                    byref(input_data), byref(errors))
        if errors:
            return SimulationCore.make_resp(False,
                                            TD_UPDATE_SRCDATA_PCK_ERROR,
                                            'Error updating cloud data',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True,
                                        TD_UPDATE_SRCDATA_PCK_OK,
                                        'Cloud data updated successfully.')

    def load_json_schematic(self, json_file: Path, batch_size: int, step_size: float, end_time: float,
                            python_exe_path: Path, log_level: str, temp_dir: Path = Path(CUR_DIR), sweep_points: dict = None,
                            is_cloud: bool = False) -> dict:

        sweep_ids = list(sweep_points.keys())
        errors = c_char_p()
        number_of_sweeps = 0
        if sweep_ids:
            number_of_sweeps = len(sweep_ids)
            array_ctypes_sweeps = (c_char_p * number_of_sweeps)()
        else:
            array_ctypes_sweeps = c_char_p()
        for ind in range(number_of_sweeps):
            array_ctypes_sweeps[ind] = sweep_ids[ind].encode()

        if not temp_dir:
            temp_dir = Path('')

        if step_size is None:
            step_size = 0
        if end_time is None:
            end_time = 0

        number_of_batches = self._LoadJsonSchematic(c_char_p(str(json_file).encode()), c_size_t(batch_size),
                                                    c_double(step_size), c_double(end_time), byref(errors),
                                                    c_char_p(str(python_exe_path).encode()), c_char_p(log_level.encode()),
                                                    c_char_p(str(temp_dir).encode()), array_ctypes_sweeps,
                                                    c_size_t(number_of_sweeps), c_bool(is_cloud))

        number_of_nodes = self.get_number_of_nodes()
        if errors:
            return SimulationCore.make_resp(False,
                                            TD_SCHEMATIC_LOAD_ERROR,
                                            'Error loading schematic',
                                            error=json.loads(errors.value.decode()))

        data = {'numberOfBatches': number_of_batches, 'numberOfNodes': number_of_nodes,
                'batchSize': batch_size}
        if sweep_points:
            data['parametricSweeps'] = sweep_points

        self._build_metadata()
        return SimulationCore.make_resp(True, TD_SCHEMATIC_LOADED, 'Schematic Loaded', data=data)

    def load_models(self):
        errors = c_char_p()
        # This ensures that DLL loading mechanism gets reset to its default behavior, which is altered when the
        #  SDK launches in Twin Deployer built with PyInstaller.
        # If this is not reset, optislang FMUs don't load because their dependent DLLs (from the binaries/win64)
        #  are not found.
        # See https://github.com/pyinstaller/pyinstaller/issues/3795
        if platform.system() == 'Windows':
            win32api.SetDllDirectory(None)
        self._LoadModels(byref(errors))
        if errors:
            return SimulationCore.make_resp(False,
                                            TD_MODELS_LOAD_ERROR,
                                            'Error loading models',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True, TD_MODELS_LOADED, 'Models Loaded')

    def close_models(self):
        errors = c_char_p()
        self._CloseModels(byref(errors))
        if errors:
            return SimulationCore.make_resp(False,
                                            TD_CLOSE_MODEL_ERROR,
                                            'Failed to close models',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True, TD_CLOSE_MODEL_OK, 'Models Closed')

    def close_schematic(self):
        errors = c_char_p()
        self._CloseJsonSchematic(byref(errors))
        if errors:
            return SimulationCore.make_resp(False,
                                            TD_CLOSE_SCHEMATIC_ERROR,
                                            'Failed to close schematic',
                                            error=json.loads(errors.value.decode()))
        self._clean_metadata()
        return SimulationCore.make_resp(True, TD_CLOSE_SCHEMATIC_OK, 'Schematic Closed')

    def set_parameters(self, node_id: str, params: Dict[str, float], sweep_id: str = ''):
        errors = c_char_p()
        num_params = len(params)
        array_ctypes_param_names = (c_char_p * num_params)()
        array_ctypes_param_values = (c_double * num_params)()

        for ind, (name, value) in enumerate(params.items()):
            array_ctypes_param_names[ind] = name.encode()
            array_ctypes_param_values[ind] = value

        self._SetParameters(c_char_p(sweep_id.encode()), c_char_p(node_id.encode()),
                            array_ctypes_param_names, array_ctypes_param_values,
                            c_size_t(num_params), byref(errors))

        if errors:
            return SimulationCore.make_resp(False,
                                            TD_SET_PARAMETERS_ERROR,
                                            'Error setting parameters',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True, TD_SET_PARAMETERS_OK, 'Parameters Set')

    def set_input_start_value(self, node_id: str, input_values: Dict[str, float]):
        errors = c_char_p()
        num_inputs = len(input_values)
        array_ctypes_input_names = (c_char_p * num_inputs)()
        array_ctypes_input_values = (c_double * num_inputs)()

        for ind, (name, value) in enumerate(input_values.items()):
            array_ctypes_input_names[ind] = name.encode()
            array_ctypes_input_values[ind] = value

        self._SetInputStartValues(c_char_p(node_id.encode()),
                                  array_ctypes_input_names, array_ctypes_input_values,
                                  c_size_t(num_inputs), byref(errors))

        if errors:
            return SimulationCore.make_resp(False,
                                            TD_SET_INPUT_START_VALUES_ERROR,
                                            'Error setting input start value',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True, TD_SET_INPUT_START_VALUES_OK, 'Inputs start values set')

    def get_number_of_nodes(self):
        number_of_nodes = self._GetNumberOfNodes()
        return number_of_nodes

    def get_rom_resource_directory(self, node_id: str, rom_name: str, instance_id: str = ''):
        errors = c_char_p()
        rom_resource_directory = self._GetRomResourceDirectory(c_char_p(instance_id.encode()),
                                                               c_char_p(node_id.encode()),
                                                               c_char_p(rom_name.encode()),
                                                               byref(errors))
        data = {'romResourcePath': rom_resource_directory.decode()}
        if errors:
            return SimulationCore.make_resp(False,
                                            TD_GET_ROM_RESOURCE_DIR_ERROR,
                                            'Error retrieving the ROM resource directory',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True, TD_GET_ROM_RESOURCE_DIR_OK, 'ROM resource path retrieved', data=data)

    def set_rom_visualization_output_directory(self, node_id: str, rom_name: str, path: str, sweep_id: str = ''):
        errors = c_char_p()

        sweep_id_c = c_char_p(sweep_id.encode())
        node_id_c = c_char_p(node_id.encode())
        rom_name_c = c_char_p(rom_name.encode())
        path_c = c_char_p(str(path).encode())
        self._SetRomVisualizationDirectory(sweep_id_c, node_id_c, rom_name_c, path_c, byref(errors))

        if errors:
            return SimulationCore.make_resp(False,
                                            TD_SET_ROM_VISUALIZATION_DIRECTORY_ERROR,
                                            'Error setting ROM visualization output directory',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True,
                                        TD_SET_ROM_VISUALIZATION_DIRECTORY_OK,
                                        'ROM visualization output directory set')

    def set_rom_visualization_state(self, node_id: str, rom_name: str, data: ROMState):
        errors = c_char_p()
        if data.vis_type == VisualizationTypes.IMAGE:
            num_views = len(data.views)
            if num_views == 0:
                return SimulationCore.make_resp(False,
                                                TD_ROM_VISUALIZATION_CHANGE_ERROR,
                                                'List of ROM views is empty',
                                                )
            views_c = (c_char_p * num_views)()
            for ind, name in enumerate(data.views):
                views_c[ind] = name.encode()
            if data.enable:
                self._EnableRomImageGeneration(c_char_p(node_id.encode()), c_char_p(rom_name.encode()),
                                               views_c, c_size_t(num_views), byref(errors))
            else:
                self._DisableRomImageGeneration(c_char_p(node_id.encode()), c_char_p(rom_name.encode()),
                                                views_c, c_size_t(num_views), byref(errors))
        elif data.vis_type == VisualizationTypes.BIN:
            if data.enable:
                self._Enable3DRomImageGeneration(c_char_p(node_id.encode()),
                                                 c_char_p(rom_name.encode()),
                                                 byref(errors))
            else:
                self._Disable3DRomImageGeneration(c_char_p(node_id.encode()),
                                                  c_char_p(rom_name.encode()),
                                                  byref(errors))
        else:
            return SimulationCore.make_resp(False,
                                            TD_ROM_VISUALIZATION_CHANGE_ERROR,
                                            f'Invalid visualization type for {rom_name}: {data.vis_type}',
                                            )

        if errors:
            return SimulationCore.make_resp(False,
                                            TD_ROM_VISUALIZATION_CHANGE_ERROR,
                                            'Error while changing the ROM visualization state',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True,
                                        TD_ROM_VISUALIZATION_CHANGE_OK,
                                        'ROM visualization state changed')

    def get_rom_image_files(self, node_id, rom_name, views, time_from=None, time_to=None, sweep_id=''):
        errors = c_char_p()
        node_id_c = c_char_p(node_id.encode())
        sweep_id_c = EMPTY_STRING_C

        n_views_c = c_size_t(len(views))
        views_array_c = (c_char_p * len(views))()
        for ind, view_name in enumerate(views):
            views_array_c[ind] = view_name.encode()

        if time_from is None:
            time_from = -1
        if time_to is None:
            time_to = -1

        num_files_c = c_size_t()
        self._GetNumRomImageFiles(sweep_id_c,
                                  node_id_c,
                                  c_char_p(rom_name.encode()),
                                  views_array_c,
                                  n_views_c,
                                  c_double(time_from),
                                  c_double(time_to),
                                  byref(num_files_c),
                                  byref(errors)
                                  )

        image_files_c = (c_char_p * num_files_c.value)()
        self._GetRomImageFiles(sweep_id_c,
                                  node_id_c,
                                  c_char_p(rom_name.encode()),
                                  views_array_c,
                                  n_views_c,
                                  c_double(time_from),
                                  c_double(time_to),
                                  byref(image_files_c),
                                  byref(errors)
                                  )
        data = {'fileList': [x.decode() for x in image_files_c]}
        return SimulationCore.make_resp(True, TD_GET_ROM_IMAGE_FILES_OK, 'ROM output files retrieved', data=data)

    def get_rom_mode_coef_files(self, node_id, rom_name, time_from=None, time_to=None, sweep_id=''):
        errors = c_char_p()
        node_id_c = c_char_p(node_id.encode())
        sweep_id_c = EMPTY_STRING_C

        if time_from is None:
            time_from = -1
        if time_to is None:
            time_to = -1

        num_files_c = c_size_t()
        self._GetNumRomModeCoefFiles(sweep_id_c,
                                  node_id_c,
                                  c_char_p(rom_name.encode()),
                                  c_double(time_from),
                                  c_double(time_to),
                                  byref(num_files_c),
                                  byref(errors)
                                  )

        image_files_c = (c_char_p * num_files_c.value)()
        self._GetRomModeCoefFiles(sweep_id_c,
                                  node_id_c,
                                  c_char_p(rom_name.encode()),
                                  c_double(time_from),
                                  c_double(time_to),
                                  byref(image_files_c),
                                  byref(errors)
                                  )

        data = {'fileList': [x.decode() for x in image_files_c]}
        return SimulationCore.make_resp(True, TD_GET_ROM_MODE_COEF_FILES_OK, 'ROM output files retrieved', data=data)

    def simulate(self):
        errors = c_char_p()
        self._Simulate(byref(errors))
        if errors:
            return SimulationCore.make_resp(False,
                                            TD_SIMULATE_ERROR,
                                            'Error during simulation',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True, TD_SIMULATE_OK, 'Simulation Successful')

    def get_result_json(self, node_id: str, sweep_ids: List[str]=None):
        errors = c_char_p()
        node_id_c = c_char_p(node_id.encode())
        sweep_id_c = EMPTY_STRING_C
        data_size = self._GetDataSize(node_id_c)
        data_size_c = c_size_t(data_size)

        data = (c_double * data_size)()
        self._GetDataForSocket(node_id_c, TIME_LABEL_C, sweep_id_c, data_size_c, data)
        time_values_py = np.array(data).tolist()
        result = {'Time': time_values_py}
        number_of_sockets = self._GetNodeOutputNumber(node_id_c)
        socket_names = (c_char_p * number_of_sockets)()
        self._GetNodeOutputs(node_id_c, socket_names)
        output_socket_ids = [x.decode() for x in socket_names]
        for socket_id in output_socket_ids:
            self._GetDataForSocket(node_id_c, c_char_p(socket_id.encode()),
                                   sweep_id_c, data_size_c, data)
            result[socket_id] = np.array(data).tolist()

        parametric_results = {}
        if sweep_ids:
            for sweep_id in sweep_ids:
                sweep_result = {}
                for socket_id in output_socket_ids:
                    self._GetDataForSocket(node_id_c, c_char_p(socket_id.encode()),
                                            c_char_p(sweep_id.encode()), data_size_c, data)
                    sweep_result[socket_id] = np.array(data).tolist()
                parametric_results[sweep_id] = sweep_result

        data = {'nodeId': node_id, 'result': result, 'parametric': parametric_results}
        if errors:
            return SimulationCore.make_resp(False,
                                            TD_GET_RESULT_ERROR,
                                            'Error retrieving results',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True, TD_GET_RESULT_OK, 'Results retrieved', data=data)

    def get_statistics(self):
        summary = self._GetSimulationSummary()
        data = json.loads(summary.decode())

        return SimulationCore.make_resp(True, TD_GET_STATISTICS_OK, 'Statistics Retrieved', data=data)

    def reset_models(self):
        errors = c_char_p()
        self._ResetModels(byref(errors))

        if errors:
            return SimulationCore.make_resp(False,
                                            TD_RESET_MODEL_ERROR,
                                            'Failed to reset models',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True, TD_RESET_MODEL_OK, 'Models Reset')

    def get_log_contents(self, node_id: str, lines_to_retrieve: int):
        errors = c_char_p()
        has_mode_data = c_bool()
        total_log_lines = c_size_t()
        log_content = self._GetLogContents(c_char_p(node_id.encode()), byref(has_mode_data), byref(total_log_lines),
                                           c_size_t(lines_to_retrieve), byref(errors))

        data = {'hasMoreData': has_mode_data.value,
                'totalNumberOfLines': total_log_lines.value,
                'logContent': log_content.decode()}
        if errors:
            return SimulationCore.make_resp(False,
                                            TD_GET_LOG_CONTENTS_ERROR,
                                            'Error retrieving log contents',
                                            error=json.loads(errors.value.decode()))
        return SimulationCore.make_resp(True, TD_GET_LOG_CONTENTS_OK, 'Log Contents Retrieved', data=data)


def build_ctype_2d_array_from_records(num_input_rows, number_of_columns, data: List[Dict]):
    input_data = (POINTER(c_double) * num_input_rows)()

    row_size = c_double * number_of_columns
    for i in range(num_input_rows):
        # Allocate arrays of double
        v = data[i].values()
        input_data[i] = row_size(*v)

    return input_data