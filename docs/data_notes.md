## Clinical data:

- Dropped 137 columns that were under 5% filled, and none were needed
  - `treatments.course_number`**:** 4.8%. It only numbers treatment courses, which you don’t need.
  - `diagnoses.days_to_last_follow_up`**,** `diagnoses.progression_or_recurrence`**,** `diagnoses.last_known_disease_status`**:** about 0.04% each, so roughly 2 rows out of 5,546. Follow-up and recurrence data are in your `follow_up.tsv`, which is where I’d get them anyway.
  - `diagnoses.figo_stage`**,** `tumor_grade`**,** `year_of_birth`**:** about 2 to 4 rows each. Too sparse to use, and your stage comes from the AJCC columns you kept.


## Phase 3.2: 
- "label alignment verified against receptors (ER, HER2)"