import os
import pytest
import pandas as pd
from pytwin.evaluate import TwinModel
from pytwin.evaluate import TwinModelError
from pytwin.settings import reinit_settings_for_unit_tests
from pytwin.settings import get_pytwin_working_dir
from pytwin.settings import get_pytwin_logger
from pytwin.settings import get_pytwin_log_file
from pytwin.settings import modify_pytwin_working_dir
from tests.utilities import compare_dictionary

COUPLE_CLUTCHES_FILEPATH = os.path.join(os.path.dirname(__file__), 'data', 'CoupledClutches_23R1_other.twin')

UNIT_TEST_WD = os.path.join(os.path.dirname(__file__), 'unit_test_wd')


def reinit_settings():
    from pytwin.settings import reinit_settings_for_unit_tests
    import shutil
    reinit_settings_for_unit_tests()
    if os.path.exists(UNIT_TEST_WD):
        shutil.rmtree(UNIT_TEST_WD)
    return UNIT_TEST_WD


class TestTwinModel:

    def test_instantiation_with_valid_model_filepath(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        TwinModel(model_filepath=model_filepath)

    def test_instantiation_with_invalid_model_filepath(self):
        with pytest.raises(TwinModelError) as e:
            TwinModel(model_filepath=None)
        assert 'Please provide valid filepath' in str(e)
        with pytest.raises(TwinModelError) as e:
            TwinModel(model_filepath='')
        assert 'Please provide existing filepath' in str(e)

    def test_parameters_property(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        # Test parameters have starting values JUST AFTER INSTANTIATION
        parameters_ref = {'CoupledClutches1_Inert1_J': 1.0,
                          'CoupledClutches1_Inert2_J': 1.0,
                          'CoupledClutches1_Inert3_J': 1.0,
                          'CoupledClutches1_Inert4_J': 1.0}
        assert compare_dictionary(twin.parameters, parameters_ref)
        # Test parameters have been well updated AFTER FIRST EVALUATION INITIALIZATION
        new_parameters = {'CoupledClutches1_Inert1_J': 3.0,
                          'CoupledClutches1_Inert2_J': 2.0}
        twin.initialize_evaluation(parameters=new_parameters)
        parameters_ref = {'CoupledClutches1_Inert1_J': 3.0,
                          'CoupledClutches1_Inert2_J': 2.0,
                          'CoupledClutches1_Inert3_J': 1.0,
                          'CoupledClutches1_Inert4_J': 1.0}
        assert compare_dictionary(twin.parameters, parameters_ref)
        # Test parameters keep same values AFTER STEP BY STEP EVALUATION
        twin.evaluate_step_by_step(step_size=0.001)
        parameters_ref = {'CoupledClutches1_Inert1_J': 3.0,
                          'CoupledClutches1_Inert2_J': 2.0,
                          'CoupledClutches1_Inert3_J': 1.0,
                          'CoupledClutches1_Inert4_J': 1.0}
        assert compare_dictionary(twin.parameters, parameters_ref)
        # Test parameters have been updated to starting values AFTER NEW INITIALIZATION
        twin.initialize_evaluation()
        parameters_ref = {'CoupledClutches1_Inert1_J': 1.0,
                          'CoupledClutches1_Inert2_J': 1.0,
                          'CoupledClutches1_Inert3_J': 1.0,
                          'CoupledClutches1_Inert4_J': 1.0}
        assert compare_dictionary(twin.parameters, parameters_ref)

    def test_inputs_property_with_step_by_step_eval(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        # Test inputs have starting values JUST AFTER INSTANTIATION
        inputs_ref = {'Clutch1_in': 0.0,
                      'Clutch2_in': 0.0,
                      'Clutch3_in': 0.0,
                      'Torque_in': 0.0}
        assert compare_dictionary(twin.inputs, inputs_ref)
        # Test inputs have been well updated AFTER FIRST EVALUATION INITIALIZATION
        new_inputs = {'Clutch1_in': 1.0,
                      'Clutch2_in': 1.0,
                      'Clutch3_in': 1.0}
        twin.initialize_evaluation(inputs=new_inputs)
        inputs_ref = {'Clutch1_in': 1.0,
                      'Clutch2_in': 1.0,
                      'Clutch3_in': 1.0,
                      'Torque_in': 0.0}
        assert compare_dictionary(twin.inputs, inputs_ref)
        # Test inputs have been well updated AFTER STEP BY STEP EVALUATION
        new_inputs = {'Clutch1_in': 2.0,
                      'Clutch2_in': 2.0}
        twin.evaluate_step_by_step(step_size=0.001, inputs=new_inputs)
        inputs_ref = {'Clutch1_in': 2.0,
                      'Clutch2_in': 2.0,
                      'Clutch3_in': 1.0,
                      'Torque_in': 0.0}
        assert compare_dictionary(twin.inputs, inputs_ref)
        new_inputs = {'Clutch1_in': 3.0}
        twin.evaluate_step_by_step(step_size=0.001, inputs=new_inputs)
        inputs_ref = {'Clutch1_in': 3.0,
                      'Clutch2_in': 2.0,
                      'Clutch3_in': 1.0,
                      'Torque_in': 0.0}
        assert compare_dictionary(twin.inputs, inputs_ref)
        # Test inputs have been set to starting values AFTER NEW INITIALIZATION
        twin.initialize_evaluation()
        inputs_ref = {'Clutch1_in': 0.0,
                      'Clutch2_in': 0.0,
                      'Clutch3_in': 0.0,
                      'Torque_in': 0.0}
        assert compare_dictionary(twin.inputs, inputs_ref)
        # Test inputs have been well updated after step by step evaluation
        new_inputs = {'Clutch1_in': 2.0,
                      'Clutch2_in': 2.0}
        twin.evaluate_step_by_step(step_size=0.001, inputs=new_inputs)
        inputs_ref = {'Clutch1_in': 2.0,
                      'Clutch2_in': 2.0,
                      'Clutch3_in': 0.0,
                      'Torque_in': 0.0}
        assert compare_dictionary(twin.inputs, inputs_ref)

    def test_inputs_and_parameters_initialization(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        # TEST DEFAULT VALUES BEFORE FIRST INITIALIZATION
        inputs_default = {'Clutch1_in': 0.0,
                          'Clutch2_in': 0.0,
                          'Clutch3_in': 0.0,
                          'Torque_in': 0.0}
        parameters_default = {'CoupledClutches1_Inert1_J': 1.0,
                              'CoupledClutches1_Inert2_J': 1.0,
                              'CoupledClutches1_Inert3_J': 1.0,
                              'CoupledClutches1_Inert4_J': 1.0}
        assert compare_dictionary(twin.inputs, inputs_default)
        assert compare_dictionary(twin.parameters, parameters_default)
        # TEST INITIALIZATION UPDATES VALUES
        inputs = {'Clutch1_in': 1.0,
                  'Clutch2_in': 1.0,
                  'Clutch3_in': 1.0,
                  'Torque_in': 1.0}
        parameters = {'CoupledClutches1_Inert1_J': 2.0,
                      'CoupledClutches1_Inert2_J': 2.0,
                      'CoupledClutches1_Inert3_J': 2.0,
                      'CoupledClutches1_Inert4_J': 2.0}
        twin.initialize_evaluation(parameters=parameters, inputs=inputs)
        assert compare_dictionary(twin.inputs, inputs)
        assert compare_dictionary(twin.parameters, parameters)
        # TEST NEW INITIALIZATION OVERRIDES PREVIOUS VALUES IF GIVEN.
        # OTHERWISE, RESET VALUES TO DEFAULT.
        new_inputs = {'Clutch1_in': 2.0,
                      'Clutch2_in': 2.0}
        new_parameters = {'CoupledClutches1_Inert1_J': 3.0,
                          'CoupledClutches1_Inert2_J': 3.0}
        twin.initialize_evaluation(parameters=new_parameters, inputs=new_inputs)
        new_inputs_ref = {'Clutch1_in': 2.0,
                          'Clutch2_in': 2.0,
                          'Clutch3_in': 0.0,
                          'Torque_in': 0.0}
        new_parameters_ref = {'CoupledClutches1_Inert1_J': 3.0,
                              'CoupledClutches1_Inert2_J': 3.0,
                              'CoupledClutches1_Inert3_J': 1.0,
                              'CoupledClutches1_Inert4_J': 1.0}
        assert compare_dictionary(twin.inputs, new_inputs_ref)
        assert compare_dictionary(twin.parameters, new_parameters_ref)
        # TEST NEW INITIALIZATION RESET VALUES TO DEFAULT IF NOT GIVEN (ALL NONE)
        twin.initialize_evaluation()
        assert compare_dictionary(twin.inputs, inputs_default)
        assert compare_dictionary(twin.parameters, parameters_default)
        # TEST NEW INITIALIZATION RESET VALUES TO DEFAULT IF NOT GIVEN (PARAMETER ONLY, INPUT=NONE --> DEFAULT)
        twin.initialize_evaluation(parameters=new_parameters, inputs=new_inputs)
        assert compare_dictionary(twin.inputs, new_inputs_ref)
        assert compare_dictionary(twin.parameters, new_parameters_ref)
        twin.initialize_evaluation(parameters=new_parameters)
        assert compare_dictionary(twin.inputs, inputs_default)
        assert compare_dictionary(twin.parameters, new_parameters_ref)
        # TEST NEW INITIALIZATION RESET VALUES TO DEFAULT IF NOT GIVEN (INPUTS ONLY, PARAMETER=NONE --> DEFAULT)
        twin.initialize_evaluation(parameters=new_parameters, inputs=new_inputs)
        assert compare_dictionary(twin.inputs, new_inputs_ref)
        assert compare_dictionary(twin.parameters, new_parameters_ref)
        twin.initialize_evaluation(inputs=new_inputs)
        assert compare_dictionary(twin.inputs, new_inputs_ref)
        assert compare_dictionary(twin.parameters, parameters_default)

    def test_inputs_property_with_batch_eval(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        # Test inputs after BATCH EVALUATION
        twin.initialize_evaluation()
        twin.evaluate_batch(pd.DataFrame({'Time': [0, 1]}))
        inputs_ref = {'Clutch1_in': 0.0,
                      'Clutch2_in': 0.0,
                      'Clutch3_in': 0.0,
                      'Torque_in': 0.0}
        assert compare_dictionary(twin.inputs, inputs_ref)

    def test_outputs_property_with_step_by_step_eval(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        # Test outputs have None values JUST AFTER INSTANTIATION
        outputs_ref = {'Clutch1_torque': None, 'Clutch2_torque': None, 'Clutch3_torque': None}
        assert compare_dictionary(twin.outputs, outputs_ref)
        # Test outputs have good values AFTER FIRST EVALUATION INITIALIZATION
        twin.initialize_evaluation()
        outputs_ref = {'Clutch1_torque': 0.0, 'Clutch2_torque': 0.0, 'Clutch3_torque': 0.0}
        assert compare_dictionary(twin.outputs, outputs_ref)
        # Test outputs have good values AFTER STEP BY STEP EVALUATION
        new_inputs = {'Clutch1_in': 1.0,
                      'Clutch2_in': 1.0}
        twin.evaluate_step_by_step(step_size=0.001, inputs=new_inputs)
        outputs_ref = {'Clutch1_torque': -10.0, 'Clutch2_torque': -5.0, 'Clutch3_torque': 0.0}
        assert compare_dictionary(twin.outputs, outputs_ref)
        # Test outputs have good values AFTER NEW EVALUATION INITIALIZATION
        twin.initialize_evaluation()
        outputs_ref = {'Clutch1_torque': 0.0, 'Clutch2_torque': 0.0, 'Clutch3_torque': 0.0}
        assert compare_dictionary(twin.outputs, outputs_ref)

    def test_outputs_property_with_batch_eval(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        # Test outputs after BATCH EVALUATION
        twin.initialize_evaluation()
        twin.evaluate_batch(pd.DataFrame({'Time': [0, 1]}))
        inputs_ref = {'Clutch1_in': 0.0,
                      'Clutch2_in': 0.0,
                      'Clutch3_in': 0.0,
                      'Torque_in': 0.0}
        outputs_ref = {'Clutch1_torque': 0.0, 'Clutch2_torque': 0.0, 'Clutch3_torque': 0.0}
        assert compare_dictionary(twin.outputs, outputs_ref)

    def test_raised_errors_with_step_by_step_evaluation(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        # Raise an error if TWIN MODEL HAS NOT BEEN INITIALIZED
        with pytest.raises(TwinModelError) as e:
            twin.evaluate_step_by_step(step_size=0.001)
        assert 'Please initialize evaluation' in str(e)
        # Raise an error if STEP SIZE IS ZERO
        with pytest.raises(TwinModelError) as e:
            twin.initialize_evaluation()
            twin.evaluate_step_by_step(step_size=0.)
        assert 'Step size must be strictly bigger than zero' in str(e)
        with pytest.raises(TwinModelError) as e:
            twin.initialize_evaluation()
            twin.evaluate_step_by_step(step_size=-0.1)
        assert 'Step size must be strictly bigger than zero' in str(e)

    def test_raised_errors_with_batch_evaluation(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        # Raise an error if TWIN MODEL HAS NOT BEEN INITIALIZED
        with pytest.raises(TwinModelError) as e:
            twin.evaluate_batch(pd.DataFrame())
        assert 'Please initialize evaluation' in str(e)
        # Raise an error if INPUTS DATAFRAME HAS NO TIME COLUMN
        with pytest.raises(TwinModelError) as e:
            twin.initialize_evaluation()
            twin.evaluate_batch(pd.DataFrame())
        assert 'Please provide a dataframe with a \'Time\' column to use batch mode evaluation' in str(e)
        # Raise an error if INPUTS DATAFRAME HAS NO TIME INSTANT ZERO
        with pytest.raises(TwinModelError) as e:
            twin.initialize_evaluation()
            twin.evaluate_batch(pd.DataFrame({'Time': [0.1]}))
        assert 'Please provide inputs at time instant t=0.s' in str(e)
        # Raise an error if INPUTS DATAFRAME HAS NO TIME INSTANT ZERO
        with pytest.raises(TwinModelError) as e:
            twin.initialize_evaluation()
            twin.evaluate_batch(pd.DataFrame({'Time': [1e-50]}))
        assert 'Please provide inputs at time instant t=0.s' in str(e)

    def test_evaluation_methods_give_same_results(self):
        inputs_df = pd.DataFrame({'Time': [0., 0.1, 0.2, 0.3],
                                  'Clutch1_in': [0., 1., 2., 3.],
                                  'Clutch2_in': [0., 1., 2., 3.]})
        sbs_outputs = {'Time': [], 'Clutch1_torque': [], 'Clutch2_torque': [], 'Clutch3_torque': []}
        # Evaluate twin model with STEP BY STEP EVALUATION
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        # t=0. (s)
        t_idx = 0
        twin.initialize_evaluation(inputs={'Clutch1_in': inputs_df['Clutch1_in'][t_idx],
                                           'Clutch2_in': inputs_df['Clutch2_in'][t_idx]})
        sbs_outputs['Time'].append(twin.evaluation_time)
        for name in twin.outputs:
            sbs_outputs[name].append(twin.outputs[name])
        for t_idx in range(1, inputs_df.shape[0]):
            # Evaluate state at instant t + step_size with inputs from instant t
            step_size = inputs_df['Time'][t_idx] - inputs_df['Time'][t_idx-1]
            new_inputs = {'Clutch1_in': inputs_df['Clutch1_in'][t_idx-1],
                          'Clutch2_in': inputs_df['Clutch2_in'][t_idx-1]}
            twin.evaluate_step_by_step(step_size=step_size, inputs=new_inputs)
            sbs_outputs['Time'].append(twin.evaluation_time)
            for name in twin.outputs:
                sbs_outputs[name].append(twin.outputs[name])
        # Evaluate twin model with BATCH EVALUATION
        twin.initialize_evaluation(inputs={'Clutch1_in': inputs_df['Clutch1_in'][0],
                                           'Clutch2_in': inputs_df['Clutch2_in'][0]})
        outputs_df = twin.evaluate_batch(inputs_df)
        # Compare STEP-BY-STEP vs BATCH RESULTS
        sbs_outputs_df = pd.DataFrame(sbs_outputs)
        assert pd.DataFrame.equals(sbs_outputs_df, outputs_df)

    def test_evaluation_initialization_with_config_file(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        # Evaluation initialization with VALID CONFIG FILE
        config_filepath = os.path.join(os.path.dirname(__file__), 'data', 'eval_init_config.json')
        twin.initialize_evaluation(json_config_filepath=config_filepath)
        inputs_ref = {'Clutch1_in': 1.0,
                      'Clutch2_in': 1.0,
                      'Clutch3_in': 1.0,
                      'Torque_in': 1.0}
        assert compare_dictionary(twin.inputs, inputs_ref)
        parameters_ref = {'CoupledClutches1_Inert1_J': 2.0,
                          'CoupledClutches1_Inert2_J': 2.0,
                          'CoupledClutches1_Inert3_J': 2.0,
                          'CoupledClutches1_Inert4_J': 2.0}
        assert compare_dictionary(twin.parameters, parameters_ref)
        # Evaluation initialization IGNORE INVALID PARAMETER AND INPUT ENTRIES
        config_filepath = os.path.join(os.path.dirname(__file__), 'data', 'eval_init_config_invalid_keys.json')
        twin.initialize_evaluation(json_config_filepath=config_filepath)
        inputs_ref = {'Clutch1_in': 1.0,
                      'Clutch2_in': 1.0,
                      'Clutch3_in': 1.0,
                      'Torque_in': 0.0}
        assert compare_dictionary(twin.inputs, inputs_ref)
        parameters_ref = {'CoupledClutches1_Inert1_J': 2.0,
                          'CoupledClutches1_Inert2_J': 2.0,
                          'CoupledClutches1_Inert3_J': 2.0,
                          'CoupledClutches1_Inert4_J': 1.0}
        assert compare_dictionary(twin.parameters, parameters_ref)
        # Evaluation initialization WITH ONLY PARAMETERS ENTRIES
        config_filepath = os.path.join(os.path.dirname(__file__), 'data', 'eval_init_config_only_parameters.json')
        twin.initialize_evaluation(json_config_filepath=config_filepath)
        inputs_ref = {'Clutch1_in': 0.0,
                      'Clutch2_in': 0.0,
                      'Clutch3_in': 0.0,
                      'Torque_in': 0.0}
        assert compare_dictionary(twin.inputs, inputs_ref)
        parameters_ref = {'CoupledClutches1_Inert1_J': 2.0,
                          'CoupledClutches1_Inert2_J': 2.0,
                          'CoupledClutches1_Inert3_J': 2.0,
                          'CoupledClutches1_Inert4_J': 2.0}
        assert compare_dictionary(twin.parameters, parameters_ref)
        # Evaluation initialization WITH ONLY INPUT ENTRIES
        config_filepath = os.path.join(os.path.dirname(__file__), 'data', 'eval_init_config_only_inputs.json')
        twin.initialize_evaluation(json_config_filepath=config_filepath)
        inputs_ref = {'Clutch1_in': 1.0,
                      'Clutch2_in': 1.0,
                      'Clutch3_in': 1.0,
                      'Torque_in': 1.0}
        assert compare_dictionary(twin.inputs, inputs_ref)
        parameters_ref = {'CoupledClutches1_Inert1_J': 1.0,
                          'CoupledClutches1_Inert2_J': 1.0,
                          'CoupledClutches1_Inert3_J': 1.0,
                          'CoupledClutches1_Inert4_J': 1.0}
        assert compare_dictionary(twin.parameters, parameters_ref)
        # Evaluation initialization RAISE AN ERROR IF CONFIG FILEPATH DOES NOT EXIST
        with pytest.raises(TwinModelError) as e:
            twin.initialize_evaluation(json_config_filepath='filepath_does_not_exist')
        assert 'Please provide an existing filepath to initialize the twin model evaluation' in str(e)

    def test_close_method(self):
        model_filepath = COUPLE_CLUTCHES_FILEPATH
        twin = TwinModel(model_filepath=model_filepath)
        twin = TwinModel(model_filepath=model_filepath)
        twin = TwinModel(model_filepath=model_filepath)

    def test_each_twin_model_has_a_subfolder_in_wd(self):
        # Init unit test
        reinit_settings_for_unit_tests()
        logger = get_pytwin_logger()
        # Verify a subfolder is created each time a new twin model is instantiated
        m_count = 10
        for m in range(m_count):
            model = TwinModel(model_filepath=COUPLE_CLUTCHES_FILEPATH)
        wd = get_pytwin_working_dir()
        temp = os.listdir(wd)
        assert len(os.listdir(wd)) == m_count + 2

    def test_model_dir_migration_after_modifying_wd_dir(self):
        # Init unit test
        wd = reinit_settings()
        assert not os.path.exists(wd)
        model = TwinModel(model_filepath=COUPLE_CLUTCHES_FILEPATH)
        assert os.path.split(model.model_dir)[0] == get_pytwin_working_dir()
        # Run test
        modify_pytwin_working_dir(new_path=wd)
        assert os.path.split(model.model_dir)[0] == wd
        assert len(os.listdir(wd)) == 1 + 1  # model + pytwin log
        model2 = TwinModel(model_filepath=COUPLE_CLUTCHES_FILEPATH)
        assert os.path.split(model2.model_dir)[0] == wd
        assert len(os.listdir(wd)) == 2 + 1 + 1  # 2 models + pytwin log + .temp

    def test_model_warns_at_initialization(self):
        # Init unit test
        wd = reinit_settings()
        model = TwinModel(model_filepath=COUPLE_CLUTCHES_FILEPATH)
        log_file = get_pytwin_log_file()
        # Warns if given parameters have wrong names
        wrong_params = {}
        for p in model.parameters:
            wrong_params[f'{p}%'] = 0.
        model.initialize_evaluation(parameters=wrong_params)
        with open(log_file, 'r') as f:
            lines = f.readlines()
        msg = 'has not been found in model parameters!'
        assert ''.join(lines).count(msg) == 4
        # Warns if given inputs have wrong names
        wrong_inputs = {}
        for i in model.inputs:
            wrong_inputs[f'{i}%'] = 0.
        model.initialize_evaluation(inputs=wrong_inputs)
        with open(log_file, 'r') as f:
            lines = f.readlines()
        msg = 'has not been found in model inputs!'
        assert ''.join(lines).count(msg) == 4

    def test_model_warns_at_evaluation_step_by_step(self):
        # Init unit test
        wd = reinit_settings()
        model = TwinModel(model_filepath=COUPLE_CLUTCHES_FILEPATH)
        log_file = get_pytwin_log_file()
        model.initialize_evaluation()
        # Warns if given inputs have wrong names
        wrong_inputs = {}
        for i in model.inputs:
            wrong_inputs[f'{i}%'] = 0.
        model.evaluate_step_by_step(step_size=0.1, inputs=wrong_inputs)
        with open(log_file, 'r') as f:
            lines = f.readlines()
        msg = 'has not been found in model inputs!'
        assert ''.join(lines).count(msg) == 4

    def test_model_warns_at_evaluation_batch(self):
        # Init unit test
        wd = reinit_settings()
        model = TwinModel(model_filepath=COUPLE_CLUTCHES_FILEPATH)
        log_file = get_pytwin_log_file()
        model.initialize_evaluation()
        # Warns if given inputs have wrong names
        wrong_inputs_df = pd.DataFrame({'Time': [0., 0.1],
                                        'Clutch1_in%': [0., 1.],
                                        'Clutch2_in%': [0., 1.]})
        model.evaluate_batch(inputs_df=wrong_inputs_df)
        with open(log_file, 'r') as f:
            lines = f.readlines()
        msg = 'has not been found in model inputs!'
        assert ''.join(lines).count(msg) == 2

    def test_save_state_workflow_a(self):
        from pytwin.twin_runtime import TwinRuntime

        backup = os.path.join(os.path.dirname(__file__), 'data', 'test_state.bin')
        if os.path.exists(backup):
            os.remove(backup)

        # Save state after initialization
        rt1 = TwinRuntime(COUPLE_CLUTCHES_FILEPATH)
        rt1.twin_instantiate()
        rt1.twin_set_input_by_name(input_name='Clutch1_in', value=1.)
        rt1.twin_initialize()
        rt1_out = rt1.twin_get_output_by_name(output_name='Clutch1_torque')
        rt1.twin_save_state(backup)

        rt2 = TwinRuntime(COUPLE_CLUTCHES_FILEPATH)
        rt2.twin_instantiate()
        rt2.twin_initialize()
        rt2_out_after_init = rt2.twin_get_output_by_name(output_name='Clutch1_torque')
        rt2.twin_load_state(load_from=backup)
        rt2_out_after_load = rt2.twin_get_output_by_name(output_name='Clutch1_torque')

        assert rt2_out_after_init != rt1_out
        assert rt2_out_after_load == rt1_out

    def test_save_state_workflow_b(self):
        from pytwin.twin_runtime import TwinRuntime

        backup = os.path.join(os.path.dirname(__file__), 'data', 'test_state_b.bin')
        if os.path.exists(backup):
            os.remove(backup)

        # Save state after simulate
        temp = COUPLE_CLUTCHES_FILEPATH
        rt1 = TwinRuntime(COUPLE_CLUTCHES_FILEPATH)
        rt1.twin_instantiate()
        rt1.twin_initialize()
        rt1.twin_set_input_by_name(input_name='Clutch1_in', value=1.)
        rt1.twin_simulate(0.01)
        rt1.twin_set_input_by_name(input_name='Clutch1_in', value=2.)
        rt1.twin_simulate(0.02)
        rt1.twin_set_input_by_name(input_name='Clutch1_in', value=3.)
        rt1.twin_simulate(0.03)
        rt1.twin_set_input_by_name(input_name='Clutch1_in', value=4.)
        rt1.twin_simulate(0.04)
        rt1.twin_set_input_by_name(input_name='Clutch1_in', value=10.)
        rt1.twin_simulate(0.05)
        rt1_out = rt1.twin_get_output_by_name(output_name='Clutch1_torque')
        rt1.twin_simulate(0.051)
        rt1_out1 = rt1.twin_get_output_by_name(output_name='Clutch1_torque')
        rt1.twin_simulate(0.052)
        rt1_out2 = rt1.twin_get_output_by_name(output_name='Clutch1_torque')
        rt1.twin_simulate(0.053)
        rt1_out3 = rt1.twin_get_output_by_name(output_name='Clutch1_torque')
        rt1.twin_save_state(backup)
        rt1_out4 = rt1.twin_get_output_by_name(output_name='Clutch1_torque')

        rt2 = TwinRuntime(COUPLE_CLUTCHES_FILEPATH)
        rt2.twin_instantiate()
        rt2.twin_initialize()
        rt2.twin_load_state(load_from=backup)
        rt2.twin_set_input_by_name(input_name='Clutch1_in', value=5.)
        rt2.twin_simulate(0.05*(1+1e-10))
        rt2_out = rt2.twin_get_output_by_name(output_name='Clutch1_torque')

        rt3 = TwinRuntime(COUPLE_CLUTCHES_FILEPATH)
        rt3.twin_instantiate()
        rt3.twin_initialize()
        rt3.twin_set_input_by_name(input_name='Clutch1_in', value=5.)
        rt3.twin_simulate(0.05*(1+1e-12))
        rt3_out = rt3.twin_get_output_by_name(output_name='Clutch1_torque')

        print('hello')
        assert rt2_out_after_init != rt1_out
        assert rt2_out_after_load == rt1_out

    def test_save_state_workflow_c(self):
        from pytwin.twin_runtime import TwinRuntime

        backup = os.path.join(os.path.dirname(__file__), 'data', 'test_state_b.bin')
        if os.path.exists(backup):
            os.remove(backup)

        # Save state after simulate
        rt1 = TwinRuntime(COUPLE_CLUTCHES_FILEPATH)
        rt1.twin_instantiate()
        rt1.twin_initialize()
        val = 1.
        t = 0.
        for i in range(10):
            rt1.twin_set_input_by_name(input_name='Clutch1_in', value=val)
            rt1.twin_simulate(t+0.001)
            rt1_out = rt1.twin_get_output_by_name(output_name='Clutch1_torque')
            t += 0.001
            val += 1.
        rt1_out = rt1.twin_get_output_by_name(output_name='Clutch1_torque')
        rt1.twin_save_state(backup)

        rt2 = TwinRuntime(COUPLE_CLUTCHES_FILEPATH)
        rt2.twin_instantiate()
        rt2.twin_initialize()
        rt2_out_after_init = rt2.twin_get_output_by_name(output_name='Clutch1_torque')
        rt2.twin_set_input_by_name(input_name='Clutch1_in', value=val-1)
        rt2.twin_load_state(load_from=backup)
        rt2_out_after_load = rt2.twin_get_output_by_name(output_name='Clutch1_torque')

        assert rt2_out_after_init != rt1_out
        assert rt2_out_after_load == rt1_out

    def test_save_state_workflow_d(self):
        from pytwin.twin_runtime import TwinRuntime

        backup = os.path.join(os.path.dirname(__file__), 'data', 'test_state_d.bin')
        if os.path.exists(backup):
            os.remove(backup)

        # Save state after simulate
        dynaROM_filepath = os.path.join(os.path.dirname(__file__), 'data', 'HX_scalarDRB_23R1_other.twin')
        rt1 = TwinRuntime(dynaROM_filepath)
        rt1.twin_instantiate()
        rt1.twin_initialize()
        rt1.twin_set_input_by_name(input_name='HeatFlow', value=1)
        rt1.twin_simulate(1)
        rt1.twin_set_input_by_name(input_name='HeatFlow', value=10)
        rt1.twin_simulate(2)
        rt1.twin_set_input_by_name(input_name='HeatFlow', value=100)
        rt1.twin_simulate(3)
        rt1.twin_set_input_by_name(input_name='HeatFlow', value=1000)
        rt1.twin_simulate(4)
        rt1.twin_set_input_by_name(input_name='HeatFlow', value=10000)
        rt1.twin_simulate(5)
        rt1.twin_save_state(backup)
        rt1_out_5 = rt1.twin_get_output_by_name(output_name='Temp1')
        rt1.twin_simulate(10)
        rt1_out_10 = rt1.twin_get_output_by_name(output_name='Temp1')
        rt1.twin_simulate(40)
        rt1_out_40 = rt1.twin_get_output_by_name(output_name='Temp1')

        rt2 = TwinRuntime(dynaROM_filepath)
        rt2.twin_instantiate()
        rt2.twin_initialize()
        rt2.twin_load_state(load_from=backup)
        rt2.twin_set_input_by_name(input_name='HeatFlow', value=10000)
        rt2.twin_simulate(5*(1+1e-12))
        rt2_out_5 = rt2.twin_get_output_by_name(output_name='Temp1')
        rt2.twin_simulate(10)
        rt2_out_10 = rt2.twin_get_output_by_name(output_name='Temp1')
        rt2.twin_simulate(40)
        rt2_out_40 = rt2.twin_get_output_by_name(output_name='Temp1')

        rt3 = TwinRuntime(dynaROM_filepath)
        rt3.twin_instantiate()
        rt3.twin_initialize()
        rt3_out_init = rt3.twin_get_output_by_name(output_name='Temp1')
        rt3.twin_set_input_by_name(input_name='HeatFlow', value=10000)
        rt3.twin_simulate(5*(1+1e-12))
        rt3_out_5 = rt3.twin_get_output_by_name(output_name='Temp1')
        rt3.twin_simulate(10)
        rt3_out_10 = rt3.twin_get_output_by_name(output_name='Temp1')
        rt3.twin_simulate(40)
        rt3_out_40 = rt3.twin_get_output_by_name(output_name='Temp1')



        print('hello')

    def test_save_state_workflow_vel(self):
        from pytwin.twin_runtime import TwinRuntime

        backup = os.path.join(os.path.dirname(__file__), 'data', 'test_state_d.bin')
        if os.path.exists(backup):
            os.remove(backup)

        # Save state after simulate
        dynaROM_filepath = os.path.join(os.path.dirname(__file__), 'data', 'HX_scalarDRB_23R1_other.twin')
        rt1 = TwinRuntime(dynaROM_filepath)
        rt1.twin_instantiate()
        rt1.twin_set_input_by_name(input_name='HeatFlow', value=1)
        rt1.twin_initialize()
        rt1_out0 = rt1.twin_get_output_by_name(output_name='Temp1')
        rt1.twin_set_input_by_name(input_name='HeatFlow', value=100)
        rt1.twin_simulate(0.1)
        rt1_out1 = rt1.twin_get_output_by_name(output_name='Temp1')
        rt1.twin_simulate(0.2)
        rt1_out2 = rt1.twin_get_output_by_name(output_name='Temp1')
        rt1.twin_simulate(0.3)
        rt1_out3 = rt1.twin_get_output_by_name(output_name='Temp1')
        rt1.twin_simulate(0.4)
        rt1_out4 = rt1.twin_get_output_by_name(output_name='Temp1')
        rt1.twin_simulate(0.5)
        rt1_out5 = rt1.twin_get_output_by_name(output_name='Temp1')
        rt1.twin_save_state(backup)
        rt1_out_5 = rt1.twin_get_output_by_name(output_name='Temp1')
        rt1.twin_simulate(10)
        rt1_out_10 = rt1.twin_get_output_by_name(output_name='Temp1')
        rt1.twin_simulate(40)
        rt1_out_40 = rt1.twin_get_output_by_name(output_name='Temp1')

        rt2 = TwinRuntime(dynaROM_filepath)
        rt2.twin_instantiate()
        rt2.twin_initialize()
        rt2.twin_load_state(load_from=backup)
        rt2.twin_set_input_by_name(input_name='HeatFlow', value=10000)
        rt2.twin_simulate(5*(1+1e-12))
        rt2_out_5 = rt2.twin_get_output_by_name(output_name='Temp1')
        rt2.twin_simulate(10)
        rt2_out_10 = rt2.twin_get_output_by_name(output_name='Temp1')
        rt2.twin_simulate(40)
        rt2_out_40 = rt2.twin_get_output_by_name(output_name='Temp1')

        rt3 = TwinRuntime(dynaROM_filepath)
        rt3.twin_instantiate()
        rt3.twin_initialize()
        rt3_out_init = rt3.twin_get_output_by_name(output_name='Temp1')
        rt3.twin_set_input_by_name(input_name='HeatFlow', value=10000)
        rt3.twin_simulate(5*(1+1e-12))
        rt3_out_5 = rt3.twin_get_output_by_name(output_name='Temp1')
        rt3.twin_simulate(10)
        rt3_out_10 = rt3.twin_get_output_by_name(output_name='Temp1')
        rt3.twin_simulate(40)
        rt3_out_40 = rt3.twin_get_output_by_name(output_name='Temp1')



        print('hello')

    def test_clean_unit_test(self):
        reinit_settings()
