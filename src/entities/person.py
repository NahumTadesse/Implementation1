from dataclasses import dataclass

@dataclass
class Person:
    weight_kg: float = 80.0
    SG_per_min: float = 0.01
    p2_per_min: float = 0.025
    p3_per_min_per_signal: float = 0.000013
    Gb_mgdl: float = 100.0
    carb_ratio_g_per_unit: float = 12.0
    ke_per_min: float = 0.02
    insulin_signal_per_unit: float = 30.0
    rex_mgdl_per_min: float = 1.0

    def V_dL(self) -> float:
        return 0.16 * self.weight_kg * 10.0