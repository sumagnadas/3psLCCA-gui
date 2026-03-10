# Input Validations

All validation rules enforced across the codebase, organized by input block.

---

## Project Metadata
`project_metadata`

| Parameter | Rule |
|-----------|------|
| `description` | Non-empty string |
| `standard` | Non-empty string |
| `country` | Non-empty string |

---

## General Parameters
`general_parameters`

| Parameter | Rule |
|-----------|------|
| `service_life_years` | > 0 |
| `analysis_period_years` | > 0 |
| `analysis_period_years` vs `service_life_years` | `analysis_period_years >= service_life_years` |
| `discount_rate_percent` | >= 0 |
| `inflation_rate_percent` | >= 0 |
| `interest_rate_percent` | >= 0 |
| `investment_ratio` | 0 <= value <= 1 |
| `social_cost_of_carbon_per_mtco2e` | >= 0 |
| `currency_conversion` | > 0 |
| `construction_period_months` | > 0 |
| `construction_period_months` vs `analysis_period_years` | `construction_period_months <= analysis_period_years * 12` |
| `working_days_per_month` | > 0 |
| `working_days_per_month` vs `days_per_month` | `working_days_per_month <= days_per_month` |
| `days_per_month` | 1 <= value <= 31 |
| `use_global_road_user_calculations` | Must be exactly `True` or `False` |

---

## Vehicle Data
`traffic_and_road_data.vehicle_data`

Applies to each vehicle: `small_cars`, `big_cars`, `two_wheelers`, `o_buses`, `d_buses`, `lcv`, `hcv`, `mcv`

| Parameter | Rule |
|-----------|------|
| `vehicles_per_day` | >= 0 |
| `carbon_emissions_kgCO2e_per_km` | >= 0 |
| `accident_percentage` | >= 0 |
| `pwr` | > 0 when provided; required for `hcv` and `mcv`, must be absent for others |
| Sum of all `accident_percentage` | Must equal 100 (tolerance ±0.1) |

---

## Accident Severity Distribution
`traffic_and_road_data.accident_severity_distribution`

| Parameter | Rule |
|-----------|------|
| `fatal` | Part of sum |
| `major` | Part of sum |
| `minor` | Part of sum |
| `fatal + major + minor` | Must equal 100 (tolerance ±1e-6) |

---

## Additional Inputs
`traffic_and_road_data.additional_inputs`

| Parameter | Rule |
|-----------|------|
| `alternate_road_carriageway` | Must be a valid IRC carriageway code (checked in `input_validator.py`) |
| `carriage_width_in_m` | >= 0 |
| `road_roughness_mm_per_km` | > 0 |
| `road_rise_m_per_km` | >= 0 |
| `road_fall_m_per_km` | >= 0 |
| `additional_reroute_distance_km` | >= 0 |
| `additional_travel_time_min` | >= 0 |
| `crash_rate_accidents_per_million_km` | >= 0 |
| `work_zone_multiplier` | 0 <= value <= 1 |
| `hourly_capacity` | > 0 |
| `peak_hour_traffic_percent_per_hour` | Each value in (0, 1] when list is non-empty; sum <= 1.0; empty list is valid (no peak hours) |
| `force_free_flow_off_peak` | Must be `True` or `False` |

---

## Routine Inspection
`maintenance_and_stage_parameters.use_stage_cost.routine.inspection`

| Parameter | Rule |
|-----------|------|
| `percentage_of_initial_construction_cost_per_year` | >= 0 |
| `interval_in_years` | > 0 |

---

## Routine Maintenance
`maintenance_and_stage_parameters.use_stage_cost.routine.maintenance`

| Parameter | Rule |
|-----------|------|
| `percentage_of_initial_construction_cost_per_year` | >= 0 |
| `percentage_of_initial_carbon_emission_cost` | >= 0 |
| `interval_in_years` | > 0 |

---

## Major Inspection
`maintenance_and_stage_parameters.use_stage_cost.major.inspection`

| Parameter | Rule |
|-----------|------|
| `percentage_of_initial_construction_cost` | >= 0 |
| `interval_for_repair_and_rehabitation_in_years` | > 0 |

---

## Major Repair
`maintenance_and_stage_parameters.use_stage_cost.major.repair`

| Parameter | Rule |
|-----------|------|
| `percentage_of_initial_construction_cost` | >= 0 |
| `percentage_of_initial_carbon_emission_cost` | >= 0 |
| `interval_for_repair_and_rehabitation_in_years` | > 0 |
| `repairs_duration_months` | > 0 |

---

## Replacement Cost (Bearing and Expansion Joint)
`maintenance_and_stage_parameters.use_stage_cost.replacement_costs_for_bearing_and_expansion_joint`

| Parameter | Rule |
|-----------|------|
| `percentage_of_super_structure_cost` | >= 0 |
| `interval_of_replacement_in_years` | > 0 |
| `duration_of_replacement_in_days` | > 0 |

---

## Demolition and Disposal
`maintenance_and_stage_parameters.end_of_life_stage_costs.demolition_and_disposal`

| Parameter | Rule |
|-----------|------|
| `percentage_of_initial_construction_cost` | >= 0 |
| `percentage_of_initial_carbon_emission_cost` | >= 0 |
| `duration_for_demolition_and_disposal_in_months` | > 0 |

---

## Global RUC Block
`daily_road_user_cost_with_vehicular_emissions`
*(only when `use_global_road_user_calculations = True`)*

| Parameter | Rule |
|-----------|------|
| `total_daily_ruc` | >= 0; must be int or float |
| `total_carbon_emission.total_emission_kgCO2e` | >= 0; must be int or float |
| `use_global_road_user_calculations` in `general_parameters` | Must be `True` |

---

## WPI
`WPI`
*(only when `use_global_road_user_calculations = False`)*

All WPI values are price indices (ratio of current to base year), so **all must be > 0**.

| Sub-block | Parameters | Rule |
|-----------|-----------|------|
| `fuel_cost` | `petrol`, `diesel`, `engine_oil`, `other_oil`, `grease` | > 0; must be numeric |
| `vehicle_cost.property_damage` | All 8 vehicle keys | > 0; must be numeric |
| `vehicle_cost.tyre_cost` | All 8 vehicle keys | > 0; must be numeric |
| `vehicle_cost.spare_parts` | All 8 vehicle keys | > 0; must be numeric |
| `vehicle_cost.fixed_depreciation` | All 8 vehicle keys | > 0; must be numeric |
| `commodity_holding_cost` | All 8 vehicle keys | > 0; must be numeric |
| `vot_cost` | All 8 vehicle keys | > 0; must be numeric *(used as divisor — zero causes division by zero)* |
| `passenger_crew_cost` | `passenger_cost`, `crew_cost` | > 0; must be numeric |
| `medical_cost` | `fatal`, `major`, `minor` | > 0; must be numeric |
| `year` | — | Integer; > 0 |

> `d_buses` in vehicle input maps to `o_buses` in WPI `property_damage` lookup — there is no `d_buses` key in WPI.

---

## Ecosystem / Cross-block Rules
Enforced in `core/utils/input_validator.py`

| Rule | Condition | Severity |
|------|-----------|----------|
| `traffic_and_road_data` must be present | `use_global_road_user_calculations = False` | Error |
| `traffic_and_road_data` present but unused | `use_global_road_user_calculations = True` | Warning |
| `alternate_road_carriageway` must be a valid IRC code | Non-global mode | Error |
| `hourly_capacity` differs from IRC standard for the carriageway | Non-global mode | Info |
| All required vehicle types must be present in `vehicle_data` | Non-global mode | Error |
| Unknown vehicle type in `vehicle_data` | Not in suggestions list | Warning |
| WPI `medical_cost` index must exist for `fatal`, `major`, `minor` | Non-global mode | Error |
| WPI `property_damage` index must exist for every vehicle type | Non-global mode | Error |
| `wpi` must be provided | Non-global mode | Error |
