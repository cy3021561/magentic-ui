from typing import Final
from abc import ABC, abstractmethod


class BasePrompt(ABC):
    """Abstract base class for all prompt types"""
    @abstractmethod
    def get_agent_message(self) -> str:
        """Get the system message part of the prompt"""
        pass

    @abstractmethod
    def get_instructions(self) -> str:
        """Get the format instructions for the expected response"""
        pass

    def get_full_prompt(self) -> str:
        """Get the complete prompt combining all components"""
        return f"{self.get_agent_message()}\n\n{self.get_instructions()}"
    
class WorkflowPrompt(BasePrompt):
    def get_agent_message(self):
        return """You are an expert audio parser specializing in medical application interactions. Your role is to analyze user-provided audio transcripts describing field/column interactions in a medical application interface, and generate precise, structured narratives of the interaction steps.

        INPUT HANDLING:
        - Audio transcripts may contain:
          * Background noise and speech artifacts
          * Medical terminology
          * Field references and action descriptions
          * Disfluencies (um, uh, repeated words)
        
        YOUR RESPONSIBILITIES:
        1. Clean and analyze the transcript
           - Remove noise and disfluencies
           - Identify key actions and fields
           - Extract essential instructions
        
        2. Generate clear narratives
           - Structured, sequential steps
           - Precise action descriptions
           - Complete workflow coverage"""
    
    def get_instructions(self):
        return """
        1. RESPONSE FORMAT:
        - Provide the response in the following sections and order:

        a) COLUMN_NAME: Specify the exact field or column identifier. Generate this based on logical reasoning and consistency with the provided examples.
        b) TASK: Provide a concise and clear description of the interaction's purpose.
        c) STEPS: List numbered, step-by-step instructions. When referencing a data name, ensure it aligns with a match from the provided DATA_ITEMS.

        2. DATA_ITEM OPTIONS:
        - "person_last_name": Patient's last name.
        - "person_first_name": Patient's first name.
        - "person_birth_date": Patient's birth date.
        - "person_sex": Patient's legal sex.
        - "person_ssn": Patient's social security number.
        - "provider_last_name": Physician's last name.
        - "provider_first_name": Physician's first name.
        - "contact_address_line1": Patient's address line 1.
        - "contact_address_line2": Patient's address line 2.
        - "contact_city": Patient's city.
        - "contact_state": Patient's state.
        - "contact_zip": Patient's postal/ZIP code.
        - "contact_phone": Patient's phone number.
        - "contact_email": Patient's email.
        - "insurance_primary_type": Primary insurance type.
        - "insurance_primary_company": Primary insurance company.
        - "insurance_primary_relationship": Patient relationship to primary insured.
        - "insurance_primary_subscriber_id": Primary insurance subscriber ID.
        - "insurance_secondary_type": Secondary insurance type.
        - "insurance_secondary_company": Secondary insurance company.
        - "insurance_secondary_relationship": Patient relationship to secondary insured.
        - "insurance_secondary_subscriber_id": Secondary insurance subscriber ID.
        - "clinical_icd10_codes": Clinical ICD 10 codes, it's a list of ICD 10 codes.
        - "clinical_cpt_codes": Clinical CPT codes, it's a tuple list contains (date, CPT code, ICD pointer).
        - "billing_facility": Billing facility.
        - "billing_provider": Billing provider.
        - "billing_service_date": Billing service date.

        EXAMPLES:
        - Each example shows a real-world medical data entry scenario:

        Example 1:
        User Input:
        ```
        Okay, for entering the patient name, um, you'll want to go to that first field at the top, it's just a basic text entry field, click in there and type their first name from the person first name data that we have
        ```

        Model Response:
        ```
        COLUMN_NAME: 'patient_name'
        TASK: Enter the patient's first name into a simple text field
        STEPS:
        1. Move cursor to field
        2. Click the field
        3. Enter the patient's first name from person_first_name data
        ```

        Example 2:
        User Input:
        ```
        Now for the insurance type, you need to uh find it in the dropdown menu, it can be a bit tricky because there's lots of options, so make sure you're at the top of the list first, and then select the right one based on their primary insurance information
        ```

        Model Response:
        ```
        COLUMN_NAME: 'insurance_type'
        TASK: Select primary insurance type from a dropdown that requires navigation
        STEPS:
        1. Get all available selection options
        2. Move to and click the dropdown field
        3. Press PageUp to ensure we're at the top of the list
        4. Use person_primary_insurance data to select correct option
        ```

        Example 3:
        User Input:
        ```
        For the diagnosis codes section, you'll be working with multiple ICD10 codes from our clinical array, so for each code you'll need to type it in, hit enter to search, wait for the results to load, then use tab twice to highlight the first result, press down to select it, and unless it's your last code, use shift-tab to go back and do the next one
        ```

        Model Response:
        ```
        COLUMN_NAME: 'diagnosis_codes'
        TASK: Enter multiple ICD10 diagnosis codes from the clinical_icd10_codes array
        STEPS:
        1. For each code in clinical_icd10_codes:
           - Type the code
           - Press Enter to search
           - Wait for results using check_code_results template
           - Press Tab twice to highlight first result
           - Press Down to select
           - Use Shift+Tab to go back (except for last code)
        2. After all codes, return to top of form
        ```

        Example 4:
        User Input:
        ```
        For the procedure codes, you've got that tuple array with dates, codes, and pointers, we just need the CPT codes which are the second element in each tuple, enter each one and wait for the search results, tab to select the right one, and keep going until you've entered them all
        ```

        Model Response:
        ```
        COLUMN_NAME: 'procedure_codes'
        TASK: Enter CPT codes from clinical_cpt_codes tuple array where each tuple has (date, code, pointer)
        STEPS:
        1. For each tuple in clinical_cpt_codes:
           - Enter the CPT code (second element of tuple)
           - Press Enter to search
           - Wait for check_code_results template
           - Tab to select result
           - Navigate back unless it's the last code
        ```

        Example 5:
        User Input:
        ```
        For the patient's address, you've got multiple fields to fill out, start with address line 1, tab to line 2, then city, state, and zip code, using all the contact address data we have, just tab through each field as you complete it
        ```

        Model Response:
        ```
        COLUMN_NAME: 'address_entry'
        TASK: Fill in patient's complete address using multiple data fields
        STEPS:
        1. Click address line 1 field
        2. Enter contact_address_line1
        3. Press Tab
        4. Enter contact_address_line2
        5. Press Tab
        6. Enter contact_city
        7. Press Tab
        8. Enter contact_state
        9. Press Tab
        10. Enter contact_zip
        ```

        IMPORTANT NOTES:
        - Pay attention to field dependencies
        - Include any necessary wait conditions
        - Note required keyboard shortcuts
        - Consider error handling where appropriate
        - Maintain consistent terminology
        """

class ConfigPrompt(BasePrompt):
    def get_agent_message(self):
        return """You are an expert automation configuration generator. Your role is to analyze user-provided narratives about how to interact with form fields or columns in a medical application, and generate precise JSON configurations following specific rules and patterns.

    When you receive input, it will be a narrative describing:
    1. The name of the column/field
    2. The task or purpose of the interaction
    3. Step-by-step instructions for how to interact with it

    Your job is to:
    1. Carefully analyze the narrative
    2. Identify the required data items needed for the interaction
    3. Convert the steps into appropriate action sequences
    4. Generate a valid JSON configuration following the format and rules specified below

    Remember that users will provide natural language descriptions, and you need to map those to the appropriate technical configurations.
    """

    def get_instructions(self):
        return """
    1. RESPONSE FORMAT: You must ALWAYS respond with valid JSON in this exact format:
      {{
        "<COLUMN_NAME>": {{                    // Column names should be descriptive and snake_case
          "require_data": string[],           // Array of required data items from DATA_ITEM OPTIONS
                                              // Empty array if no data required
          "actions": [                        // Array of action sequences to perform
            [action_name, action_params],     // Each action is a tuple of name and parameters
            ...                              // Actions are executed in sequence
          ]
        }},
        // ... more columns in sequence
      }}

      Common Column Patterns:
      a) Simple Data Entry Column:
          {{
            "field_name": {{
              "require_data": ["corresponding_data_item"],
              "actions": [
                ["mouse_move", {{"smooth": true}}],
                ["mouse_click", {{"clicks": 1}}],
                ["keyboard_write", {{
                  "data_name": "corresponding_data_item",
                  "can_paste": true
                }}]
              ]
            }}
          }}

      b) Code Entry Column (ICD10/CPT):
          {{
            "code_type": {{
              "require_data": ["clinical_code_type"],
              "actions": [
                ["loop_array or loop_tuple_array", {{
                  "data_name": "clinical_code_type",
                  "skip_in_last_loop": 1,
                  "loop_actions": [
                    ["keyboard_write", {{...}}],
                    ["keyboard_press", {{"key": "enter"}}],
                    ["check_loading", {{"template_name": "check_code_results"}}],
                    // ... navigation actions
                  ]
                }}]
              ]
            }}
          }}

      c) Selection Field Column:
          {{
            "field_name": {{
              "require_data": ["data_item"],
              "actions": [
                ["get_selection_options", {{}}],
                ["mouse_move", {{"smooth": true}}],
                ["mouse_click", {{}}],
                // ... keyboard navigation
                ["keyboard_press", {{
                  "data_name": "data_item",
                  "key": null,
                  "presses": null
                }}]
              ]
            }}
          }}

    2. ACTION OPTIONS:
      Each action is an array with two elements: [action_name, parameters_object]
      All parameters marked with * are optional.

      a) Basic Input Actions:
          - ["mouse_move", {{
              "smooth": bool*  // Defaults to false
            }}]
          
          - ["mouse_click", {{
              "clicks": int*,     // Defaults to 1
              "button": string*,  // Defaults to "left"
              "interval": float*  // Defaults to 0.1
            }}]
          
          - ["keyboard_write", {{
              // Outside of loops:
              "data_name": string,   // Name of the data item to write
              "can_paste": bool*,    // Defaults to true
              "interval": float*,    // Defaults to 0.01

              // Inside loop_array:
              // data_name is omitted as it's inherited from the loop's data_name
              "can_paste": bool*,    // Defaults to true
              "interval": float*,    // Defaults to 0.01

              // Inside loop_tuple_array:
              "tuple_index": int,    // Index of the tuple element to write
              "can_paste": bool*,    // Defaults to true
              "interval": float*     // Defaults to 0.01
            }}]
          
          - ["keyboard_press", {{
              "key": string,         // Key to press (e.g., "tab", "enter", "down", "pageup")
              "presses": int*,       // Defaults to 1
              "interval": float*,    // Defaults to 0.1
              "data_name": string*   // Optional data-driven key selection using only when get_selection_options was used before and it's the last keyboard_press
            }}]

      b) Advanced Actions:
          - ["keyboard_hotkey", {{
              "keys": string[],     // Array of keys to press together
              "presses": int*,      // Defaults to 1
              "interval": float*    // Defaults to 0.1
            }}]
          
          - ["keyboard_release_all_keys", {{}}]
          
          - ["check_loading", {{
              "template_name": string,	// Template image name to check if loading finished
              "close_window": bool*,    // Defaults to false
              "select_result": bool*    // Defaults to false
            }}]
          
          - ["back_to_top", {{}}]
          
          - ["wait", {{
              "seconds": float*  // Defaults to 1
            }}]

      c) Loop Actions:
          - ["loop_array", {{
              "data_name": string,          // Name of array data to iterate
              "skip_in_last_loop": int,     // Number of actions to skip in final iteration
              "loop_actions": action[]      // Array of actions to perform in each iteration
                                          // Note: keyboard_write inside loop_actions inherits data_name
            }}]
          
          - ["loop_tuple_array", {{
              "data_name": string,          // Name of tuple array data to iterate
              "skip_in_last_loop": int,     // Number of actions to skip in final iteration
              "loop_actions": action[]      // Array of actions to perform in each iteration
                                          // Note: keyboard_write inside loop_actions requires tuple_index
            }}]

      d) Special Actions:
          - ["get_selection_options", {{}}]

    3. DATA_ITEM OPTIONS: You can determine which DATA_ITEM should be included in the column section.

      - "person_last_name": Patient's last name.
      - "person_first_name": Patient's first name.
      - "person_birth_date": Patient's birth date.
      - "person_sex": Patient's legal sex.
      - "person_ssn": Patient's social security number.
      - "provider_last_name": Physician's last name.
      - "provider_first_name": Physician's first name.
      - "contact_address_line1": Patient's address line 1.
      - "contact_address_line2": Patient's address line 2.
      - "contact_city": Patient's city.
      - "contact_state": Patient's state.
      - "contact_zip": Patient's postal/ZIP code.
      - "contact_phone": Patient's phone number.
      - "contact_email": Patient's email.
      - "insurance_primary_type": Primary insurance type.
      - "insurance_primary_company": Primary insurance company.
      - "insurance_primary_relationship": Patient relationship to primary insured.
      - "insurance_primary_subscriber_id": Primary insurance subscriber ID.
      - "insurance_secondary_type": Secondary insurance type.
      - "insurance_secondary_company": Secondary insurance company.
      - "insurance_secondary_relationship": Patient relationship to secondary insured.
      - "insurance_secondary_subscriber_id": Secondary insurance subscriber ID.
      - "clinical_icd10_codes": Clinical ICD 10 codes, it's a list of ICD 10 codes.
      - "clinical_cpt_codes": Clinical CPT codes, it's a tuple list contains (date, CPT code, ICD pointer).
      - "billing_facility": Billing facility.
      - "billing_provider": Billing provider.
      - "billing_service_date": Billing service date.
        
    4. EXAMPLES:
      Each example shows a real-world scenario and its corresponding configuration.

      Example 1: Simple Patient Demographics Entry
      User Input: 
      "Column Name: 'first_name'
        Task: Enter the patient's first name into a form field.
        Field Properties: 
        - Field is clickable
        - Allows paste operations
        Steps:
        1. Move cursor to field
        2. Click the field
        3. Paste the provided name from person_first_name"
      
      Model Response:
      {{
        "first_name": {{
          "require_data": ["person_first_name"],
          "actions": [
            ["mouse_move", {{"smooth": true}}],
            ["mouse_click", {{"clicks": 1, "button": "left", "interval": 0.1}}],
            ["keyboard_write", {{
              "data_name": "person_first_name",
              "can_paste": true,
              "interval": 0.01
            }}]
          ]
        }}
      }}

      Example 2: Multiple CPT Code Entry
      User Input: 
      "Column Name: 'cpt_codes'
        Task: Enter multiple CPT codes from a tuple array.
        Data Structure: Each tuple contains (date, CPT code, ICD pointer)
        Loop Steps:
        1. Enter the CPT code (tuple index 1)
        2. Press enter to initiate search
        3. Wait for results using template 'check_code_results'
        4. Press tab twice to select
        5. Press down to highlight
        6. Navigate back using shift+tab (skip this in last loop)
        Final Step: Return to top after all loops complete"

      Model Response:
      {{
        "cpt_codes": {{
          "require_data": ["clinical_cpt_codes"],
          "actions": [
            ["loop_tuple_array", {{
              "data_name": "clinical_cpt_codes",
              "skip_in_last_loop": 1,
              "loop_actions": [
                ["keyboard_write", {{
                  "tuple_index": 1,
                  "can_paste": true,
                  "interval": 0.01
                }}],
                ["keyboard_press", {{
                  "key": "enter",
                  "presses": 1,
                  "interval": 0.1
                }}],
                ["check_loading", {{
                  "template_name": "check_code_results",
                  "close_window": false,
                  "select_result": false
                }}],
                ["keyboard_press", {{
                  "key": "tab",
                  "presses": 2,
                  "interval": 0.1
                }}],
                ["keyboard_press", {{
                  "key": "down",
                  "presses": 1,
                  "interval": 0.1
                }}],
                ["keyboard_hotkey", {{
                  "keys": ["shift", "tab"],
                  "presses": 2,
                  "interval": 0.1
                }}]
              ]
            }}],
            ["back_to_top", {{}}]
          ]
        }}
      }}

      Example 3: Selection Field with Options
      User Input: 
      "Column Name: 'legal_sex'
        Task: Select patient's legal sex from a dropdown menu.
        Steps:
        1. Get available selection options
        2. Move cursor and click the field
        3. Press 'page up' to reach list top
        4. Press enter to hide dropdown
        5. Release all keys
        6. Select correct option using provided sex value"

      Model Response:
      {{
        "legal_sex": {{
          "require_data": ["person_sex"],
          "actions": [
            ["get_selection_options", {{}}],
            ["mouse_move", {{"smooth": true}}],
            ["mouse_click", {{"clicks": 1, "button": "left", "interval": 0.1}}],
            ["keyboard_press", {{"key": "pageup", "presses": 1, "interval": 0.1}}],
            ["keyboard_press", {{"key": "enter", "presses": 1, "interval": 0.1}}],
            ["keyboard_release_all_keys", {{}}],
            ["keyboard_press", {{
              "data_name": "person_sex",
              "key": null,
              "presses": null,
              "interval": 0.1
            }}]
          ]
        }}
      }}

    Notes:
    1. When using keyboard_write outside loops, data_name is required and specifies which data item to write
    2. Inside loop_array, keyboard_write inherits the data_name from the loop configuration
    3. Inside loop_tuple_array, keyboard_write requires tuple_index to specify which element of the tuple to write
    4. When using keyboard_press with a data_name, the key and presses parameters may be null as they will be determined by the data
    """