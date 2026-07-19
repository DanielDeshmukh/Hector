"""
Comprehensive legal accuracy tests for HECTOR IPC ↔ BNS mapping.
Validates mapping integrity, high-profile sections, consistency,
and router integration.
"""

import json
import os
import re

import pytest

from core.router import HectorRouter


@pytest.fixture(scope="module")
def mapping_data():
    path = os.path.join(os.path.dirname(__file__), os.pardir, "core", "mapping.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def ipc_to_bns(mapping_data):
    return mapping_data["IPC_TO_BNS"]


@pytest.fixture(scope="module")
def bns_to_ipc(mapping_data):
    return mapping_data["BNS_TO_IPC_REVERSE"]


@pytest.fixture(scope="module")
def router():
    return HectorRouter()


# ── Mapping Structure Tests ──────────────────────────────────────


class TestMappingStructure:
    def test_mapping_file_loads(self, mapping_data):
        assert "IPC_TO_BNS" in mapping_data
        assert "BNS_TO_IPC_REVERSE" in mapping_data

    def test_ipc_to_bns_entry_count(self, ipc_to_bns):
        assert len(ipc_to_bns) >= 485

    def test_bns_to_ipc_entry_count(self, bns_to_ipc):
        assert len(bns_to_ipc) >= 10

    def test_system_notes_present(self, mapping_data):
        notes = mapping_data.get("SYSTEM_NOTES", {})
        assert "effective_date" in notes
        assert "total_mapped" in notes

    def test_system_notes_mapped_count(self, mapping_data):
        notes = mapping_data["SYSTEM_NOTES"]
        assert notes["total_mapped"] >= 485

    def test_all_ipc_entries_have_new_field(self, ipc_to_bns):
        for sec, data in ipc_to_bns.items():
            assert "new" in data, f"IPC {sec} missing 'new'"
            assert data["new"], f"IPC {sec} has empty 'new'"

    def test_all_ipc_entries_have_name_field(self, ipc_to_bns):
        for sec, data in ipc_to_bns.items():
            assert "name" in data, f"IPC {sec} missing 'name'"
            assert data["name"], f"IPC {sec} has empty 'name'"

    def test_all_reverse_entries_have_old_field(self, bns_to_ipc):
        for sec, data in bns_to_ipc.items():
            assert "old" in data, f"BNS {sec} missing 'old'"
            assert data["old"], f"BNS {sec} has empty 'old'"

    def test_all_reverse_entries_have_name_field(self, bns_to_ipc):
        for sec, data in bns_to_ipc.items():
            assert "name" in data, f"BNS {sec} missing 'name'"


# ── High-Profile IPC → BNS Mappings ──────────────────────────────


class TestHighProfileMappings:
    def test_ipc_302_murder(self, ipc_to_bns):
        assert ipc_to_bns["302"]["new"] == "101"
        assert ipc_to_bns["302"]["name"] == "Murder"

    def test_ipc_376_rape(self, ipc_to_bns):
        assert ipc_to_bns["376"]["new"] == "178"

    def test_ipc_304_death_by_negligence(self, ipc_to_bns):
        assert ipc_to_bns["304"]["new"] == "103"
        assert ipc_to_bns["304"]["name"] == "Death by Negligence"

    def test_ipc_420_cheating(self, ipc_to_bns):
        assert ipc_to_bns["420"]["new"] == "318"
        assert ipc_to_bns["420"]["name"] == "Cheating and Dishonesty"

    def test_ipc_379_theft_punishment(self, ipc_to_bns):
        assert ipc_to_bns["379"]["new"] == "304"
        assert ipc_to_bns["379"]["name"] == "Punishment for Theft"

    def test_ipc_378_theft(self, ipc_to_bns):
        assert ipc_to_bns["378"]["new"] == "303"
        assert ipc_to_bns["378"]["name"] == "Theft"

    def test_ipc_498a_in_mapping(self, ipc_to_bns):
        assert "498A" in ipc_to_bns
        assert ipc_to_bns["498A"]["new"] == "80"

    def test_ipc_302_is_murder(self, ipc_to_bns):
        entry = ipc_to_bns["302"]
        assert entry["new"] == "101"
        assert entry["name"] == "Murder"
        assert entry.get("note") == "intentional killing"

    def test_ipc_303_culpable_homicide(self, ipc_to_bns):
        assert ipc_to_bns["303"]["new"] == "102"
        assert ipc_to_bns["303"]["name"] == "Culpable Homicide"

    def test_ipc_304a_causes_death_negligence(self, ipc_to_bns):
        assert ipc_to_bns["304A"]["new"] == "104"
        assert ipc_to_bns["304A"]["name"] == "Causing Death by Negligence"

    def test_ipc_304b_dowry_death(self, ipc_to_bns):
        assert ipc_to_bns["304B"]["new"] == "105"
        assert ipc_to_bns["304B"]["name"] == "Dowry Death"

    def test_ipc_305_abetment_suicide(self, ipc_to_bns):
        assert ipc_to_bns["305"]["new"] == "106"
        assert ipc_to_bns["305"]["name"] == "Abetment of Suicide"

    def test_ipc_306_attempt_murder(self, ipc_to_bns):
        assert ipc_to_bns["306"]["new"] == "107"
        assert ipc_to_bns["306"]["name"] == "Attempt to Murder"

    def test_ipc_307_attempt_murder(self, ipc_to_bns):
        assert ipc_to_bns["307"]["new"] == "109"
        assert ipc_to_bns["307"]["name"] == "Attempt to Murder"

    def test_ipc_308_attempt_culpable_homicide(self, ipc_to_bns):
        assert ipc_to_bns["308"]["new"] == "110"

    def test_ipc_309_attempt_suicide(self, ipc_to_bns):
        assert ipc_to_bns["309"]["new"] == "111"

    def test_ipc_120a_criminal_conspiracy(self, ipc_to_bns):
        assert ipc_to_bns["120A"]["new"] == "131"
        assert ipc_to_bns["120A"]["name"] == "Criminal Conspiracy"

    def test_ipc_120b_punishment_conspiracy(self, ipc_to_bns):
        assert ipc_to_bns["120B"]["new"] == "132"

    def test_ipc_121_waging_war(self, ipc_to_bns):
        assert ipc_to_bns["121"]["new"] == "133"
        assert ipc_to_bns["121"]["name"] == "Waging War Against Government"

    def test_ipc_124a_sedition(self, ipc_to_bns):
        assert ipc_to_bns["124A"]["new"] == "138"
        assert ipc_to_bns["124A"]["name"] == "Sedition"

    def test_ipc_144_criminal_intimidation(self, ipc_to_bns):
        assert ipc_to_bns["144"]["new"] == "158"

    def test_ipc_147_rioting(self, ipc_to_bns):
        assert ipc_to_bns["147"]["new"] == "161"

    def test_ipc_354_assault_woman(self, ipc_to_bns):
        assert ipc_to_bns["354"]["new"] == "156"
        assert ipc_to_bns["354"]["name"] == "Assault to Disrobe"

    def test_ipc_376_rapespecific(self, ipc_to_bns):
        assert ipc_to_bns["376"]["new"] == "178"
        assert ipc_to_bns["376"]["name"] == "Obscene Exposure"

    def test_ipc_392_dacoity_punishment(self, ipc_to_bns):
        assert ipc_to_bns["392"]["new"] == "316"

    def test_ipc_395_dacoity(self, ipc_to_bns):
        assert ipc_to_bns["395"]["new"] == "319"

    def test_ipc_396_dacoity_murder(self, ipc_to_bns):
        assert ipc_to_bns["396"]["new"] == "320"

    def test_ipc_406_criminal_breach_trust(self, ipc_to_bns):
        assert ipc_to_bns["406"]["new"] == "330"
        assert ipc_to_bns["406"]["name"] == "Criminal Breach of Trust"

    def test_ipc_420_is_318(self, ipc_to_bns):
        assert ipc_to_bns["420"]["new"] == "318"

    def test_ipc_425_mischief(self, ipc_to_bns):
        assert ipc_to_bns["425"]["new"] == "348"
        assert ipc_to_bns["425"]["name"] == "Mischief"

    def test_ipc_441_criminal_trespass(self, ipc_to_bns):
        assert ipc_to_bns["441"]["new"] == "364"
        assert ipc_to_bns["441"]["name"] == "Criminal Trespass"

    def test_ipc_447_punishment_trespass(self, ipc_to_bns):
        assert ipc_to_bns["447"]["new"] == "370"

    def test_ipc_498_husband_cruelty(self, ipc_to_bns):
        assert "498" in ipc_to_bns

    def test_ipc_499_defamation(self, ipc_to_bns):
        assert ipc_to_bns["499"]["new"] == "356"
        assert ipc_to_bns["499"]["name"] == "Defamation"

    def test_ipc_500_defamation_punishment(self, ipc_to_bns):
        assert ipc_to_bns["500"]["new"] == "357"

    def test_ipc_503_criminal_intimidation(self, ipc_to_bns):
        assert ipc_to_bns["503"]["new"] == "360"
        assert ipc_to_bns["503"]["name"] == "Criminal Intimidation"

    def test_ipc_504_punishment_intimidation(self, ipc_to_bns):
        assert ipc_to_bns["504"]["new"] == "361"

    def test_ipc_506_punishment_intimidation_death(self, ipc_to_bns):
        assert ipc_to_bns["506"]["new"] == "363"

    def test_ipc_509_word_gesture_woman(self, ipc_to_bns):
        assert ipc_to_bns["509"]["new"] == "366"

    def test_ipc_511_attempt_offence(self, ipc_to_bns):
        assert ipc_to_bns["511"]["new"] == "368"

    def test_ipc_14_local_jurisdiction(self, ipc_to_bns):
        assert ipc_to_bns["14"]["new"] == "2"
        assert ipc_to_bns["14"]["name"] == "Local Jurisdiction"

    def test_ipc_53_punishments(self, ipc_to_bns):
        assert ipc_to_bns["53"]["new"] == "61"
        assert ipc_to_bns["53"]["name"] == "Punishments"

    def test_ipc_82_child_under_seven(self, ipc_to_bns):
        assert ipc_to_bns["82"]["new"] == "91"
        assert ipc_to_bns["82"]["name"] == "Child Under Seven"

    def test_ipc_84_unsound_mind(self, ipc_to_bns):
        assert ipc_to_bns["84"]["new"] == "93"
        assert ipc_to_bns["84"]["name"] == "Unsound Mind"

    def test_ipc_87_act_causes_slight_harm(self, ipc_to_bns):
        assert ipc_to_bns["87"]["new"] == "96"

    def test_ipc_92_right_private_defense(self, ipc_to_bns):
        assert ipc_to_bns["92"]["new"] == "101"

    def test_ipc_100_right_cause_death(self, ipc_to_bns):
        assert ipc_to_bns["100"]["new"] == "109"

    def test_ipc_107_abetment(self, ipc_to_bns):
        assert ipc_to_bns["107"]["new"] == "116"
        assert ipc_to_bns["107"]["name"] == "Abetment"

    def test_ipc_109abetment_punishment(self, ipc_to_bns):
        assert ipc_to_bns["109"]["new"] == "119"

    def test_ipc_299_hurt(self, ipc_to_bns):
        assert ipc_to_bns["299"]["new"] == "313"
        assert ipc_to_bns["299"]["name"] == "Hurt"

    def test_ipc_300_grievous_hurt(self, ipc_to_bns):
        assert ipc_to_bns["300"]["new"] == "314"
        assert ipc_to_bns["300"]["name"] == "Grievous Hurt"

    def test_ipc_323_punishment_hurt(self, ipc_to_bns):
        assert ipc_to_bns["323"]["new"] == "125"

    def test_ipc_324_hurt_dangerous_weapon(self, ipc_to_bns):
        assert ipc_to_bns["324"]["new"] == "126"

    def test_ipc_325_grievous_hurt_weapon(self, ipc_to_bns):
        assert ipc_to_bns["325"]["new"] == "127"

    def test_ipc_330_wrongful_restraint(self, ipc_to_bns):
        assert ipc_to_bns["330"]["new"] == "132"
        assert ipc_to_bns["330"]["name"] == "Wrongful Restraint"

    def test_ipc_331_wrongful_confinement(self, ipc_to_bns):
        assert ipc_to_bns["331"]["new"] == "133"
        assert ipc_to_bns["331"]["name"] == "Wrongful Confinement"

    def test_ipc_341_punishment_restraint(self, ipc_to_bns):
        assert ipc_to_bns["341"]["new"] == "143"

    def test_ipc_342_punishment_confinement(self, ipc_to_bns):
        assert ipc_to_bns["342"]["new"] == "144"

    def test_ipc_351_assault(self, ipc_to_bns):
        assert ipc_to_bns["351"]["new"] == "153"
        assert ipc_to_bns["351"]["name"] == "Assault"

    def test_ipc_353_assault_public_servant(self, ipc_to_bns):
        assert ipc_to_bns["353"]["new"] == "155"

    def test_ipc_363_robbery(self, ipc_to_bns):
        assert ipc_to_bns["363"]["new"] == "165"

    def test_ipc_364_dacoity_murder(self, ipc_to_bns):
        assert ipc_to_bns["364"]["new"] == "166"

    def test_ipc_366_kidnapping(self, ipc_to_bns):
        assert ipc_to_bns["366"]["new"] == "168"

    def test_ipc_369_theft(self, ipc_to_bns):
        assert ipc_to_bns["369"]["new"] == "171"

    def test_ipc_370_stolen_property(self, ipc_to_bns):
        assert ipc_to_bns["370"]["new"] == "172"

    def test_ipc_376a_rape_public_servant(self, ipc_to_bns):
        assert "376A" not in ipc_to_bns

    def test_ipc_380_theft_dwelling(self, ipc_to_bns):
        assert ipc_to_bns["380"]["new"] == "305"

    def test_ipc_381_theft_servant(self, ipc_to_bns):
        assert ipc_to_bns["381"]["new"] == "306"

    def test_ipc_383_extortion(self, ipc_to_bns):
        assert ipc_to_bns["383"]["new"] == "308"

    def test_ipc_384_punishment_extortion(self, ipc_to_bns):
        assert ipc_to_bns["384"]["new"] == "309"

    def test_ipc_386_extortion_death_threat(self, ipc_to_bns):
        assert ipc_to_bns["386"]["new"] == "311"

    def test_ipc_388_extortionrobbery(self, ipc_to_bns):
        assert ipc_to_bns["388"]["new"] == "313"

    def test_ipc_390_dacoity(self, ipc_to_bns):
        assert ipc_to_bns["390"]["new"] == "315"

    def test_ipc_391_dacoity_definition(self, ipc_to_bns):
        assert ipc_to_bns["391"]["new"] == "310"

    def test_ipc_397_robbery_dacoity(self, ipc_to_bns):
        assert ipc_to_bns["397"]["new"] == "321"

    def test_ipc_403_dishonest_misappropriation(self, ipc_to_bns):
        assert ipc_to_bns["403"]["new"] == "327"

    def test_ipc_404_criminal_misappropriation(self, ipc_to_bns):
        assert ipc_to_bns["404"]["new"] == "328"

    def test_ipc_407_breach_trust_punishment(self, ipc_to_bns):
        assert ipc_to_bns["407"]["new"] == "331"

    def test_ipc_408_breach_trust_clerk(self, ipc_to_bns):
        assert ipc_to_bns["408"]["new"] == "332"

    def test_ipc_409_public_servant_trust(self, ipc_to_bns):
        assert ipc_to_bns["409"]["new"] == "333"

    def test_ipc_410_receiving_stolen(self, ipc_to_bns):
        assert ipc_to_bns["410"]["new"] == "334"

    def test_ipc_411_habitual_receiving(self, ipc_to_bns):
        assert ipc_to_bns["411"]["new"] == "335"

    def test_ipc_414_habitual_stolen(self, ipc_to_bns):
        assert ipc_to_bns["414"]["new"] == "338"

    def test_ipc_415_cheating_definition(self, ipc_to_bns):
        assert ipc_to_bns["415"]["new"] == "339"

    def test_ipc_417_cheating_punishment(self, ipc_to_bns):
        assert ipc_to_bns["417"]["new"] == "341"

    def test_ipc_418_cheating_false_document(self, ipc_to_bns):
        assert ipc_to_bns["418"]["new"] == "342"

    def test_ipc_419_cheating_by_personation(self, ipc_to_bns):
        assert ipc_to_bns["419"]["new"] == "343"

    def test_ipc_421_fraudulent_deed(self, ipc_to_bns):
        assert ipc_to_bns["421"]["new"] == "344"

    def test_ipc_422_fraudulent_removal(self, ipc_to_bns):
        assert ipc_to_bns["422"]["new"] == "345"

    def test_ipc_423_breach_contract(self, ipc_to_bns):
        assert ipc_to_bns["423"]["new"] == "346"

    def test_ipc_424_fraudulent_removal2(self, ipc_to_bns):
        assert ipc_to_bns["424"]["new"] == "347"

    def test_ipc_426_mischief_punishment(self, ipc_to_bns):
        assert ipc_to_bns["426"]["new"] == "349"

    def test_ipc_427_mischief_damage(self, ipc_to_bns):
        assert ipc_to_bns["427"]["new"] == "350"

    def test_ipc_428_killing_animal(self, ipc_to_bns):
        assert ipc_to_bns["428"]["new"] == "351"

    def test_ipc_429_mischief_fire(self, ipc_to_bns):
        assert ipc_to_bns["429"]["new"] == "352"

    def test_ipc_430_mischief_explosion(self, ipc_to_bns):
        assert ipc_to_bns["430"]["new"] == "353"

    def test_ipc_435_mischief_house(self, ipc_to_bns):
        assert ipc_to_bns["435"]["new"] == "358"

    def test_ipc_436_mischief_flood_poison(self, ipc_to_bns):
        assert ipc_to_bns["436"]["new"] == "359"

    def test_ipc_440_house_trespass(self, ipc_to_bns):
        assert ipc_to_bns["440"]["new"] == "363"

    def test_ipc_442_house_trespass_definition(self, ipc_to_bns):
        assert ipc_to_bns["442"]["new"] == "365"

    def test_ipc_443_lurking_trespass(self, ipc_to_bns):
        assert ipc_to_bns["443"]["new"] == "366"

    def test_ipc_444_house_breaking(self, ipc_to_bns):
        assert ipc_to_bns["444"]["new"] == "367"

    def test_ipc_445_house_breaking_night(self, ipc_to_bns):
        assert ipc_to_bns["445"]["new"] == "368"

    def test_ipc_446_house_breaking_warning(self, ipc_to_bns):
        assert ipc_to_bns["446"]["new"] == "369"

    def test_ipc_448_house_trespass_temple(self, ipc_to_bns):
        assert ipc_to_bns["448"]["new"] == "371"

    def test_ipc_449_trespass_for_offence(self, ipc_to_bns):
        assert ipc_to_bns["449"]["new"] == "372"

    def test_ipc_450_trespass_hurt(self, ipc_to_bns):
        assert ipc_to_bns["450"]["new"] == "373"

    def test_ipc_451_trespass_notice(self, ipc_to_bns):
        assert ipc_to_bns["451"]["new"] == "374"

    def test_ipc_452_criminal_force(self, ipc_to_bns):
        assert ipc_to_bns["452"]["new"] == "375"

    def test_ipc_453_punishment_force(self, ipc_to_bns):
        assert ipc_to_bns["453"]["new"] == "376"

    def test_ipc_455_assault_punishment(self, ipc_to_bns):
        assert ipc_to_bns["455"]["new"] == "378"

    def test_ipc_456_assault_woman(self, ipc_to_bns):
        assert ipc_to_bns["456"]["new"] == "379"

    def test_ipc_457_assault_with_intent(self, ipc_to_bns):
        assert ipc_to_bns["457"]["new"] == "380"

    def test_ipc_458_force_public_servant(self, ipc_to_bns):
        assert ipc_to_bns["458"]["new"] == "381"

    def test_ipc_459_assault_public_servant(self, ipc_to_bns):
        assert ipc_to_bns["459"]["new"] == "382"

    def test_ipc_460_force_after_warning(self, ipc_to_bns):
        assert ipc_to_bns["460"]["new"] == "383"

    def test_ipc_461_wrongful_restraint(self, ipc_to_bns):
        assert ipc_to_bns["461"]["new"] == "384"

    def test_ipc_462_punishment_restraint(self, ipc_to_bns):
        assert ipc_to_bns["462"]["new"] == "385"

    def test_ipc_463_wrongful_confinement(self, ipc_to_bns):
        assert ipc_to_bns["463"]["new"] == "386"

    def test_ipc_464_punishment_confinement(self, ipc_to_bns):
        assert ipc_to_bns["464"]["new"] == "387"

    def test_ipc_465_confinement_3_days(self, ipc_to_bns):
        assert ipc_to_bns["465"]["new"] == "388"

    def test_ipc_466_confinement_10_days(self, ipc_to_bns):
        assert ipc_to_bns["466"]["new"] == "389"

    def test_ipc_467_confinement_public_servant(self, ipc_to_bns):
        assert ipc_to_bns["467"]["new"] == "390"

    def test_ipc_468_confinement_secret(self, ipc_to_bns):
        assert ipc_to_bns["468"]["new"] == "391"

    def test_ipc_469_confinement_extortion(self, ipc_to_bns):
        assert ipc_to_bns["469"]["new"] == "392"

    def test_ipc_470_forced_confinement(self, ipc_to_bns):
        assert ipc_to_bns["470"]["new"] == "393"

    def test_ipc_471_kidnapping(self, ipc_to_bns):
        assert ipc_to_bns["471"]["new"] == "394"

    def test_ipc_472_kidnapping_punishment(self, ipc_to_bns):
        assert ipc_to_bns["472"]["new"] == "395"

    def test_ipc_473_kidnapping_ransom(self, ipc_to_bns):
        assert ipc_to_bns["473"]["new"] == "396"

    def test_ipc_474_kidnapping_murder(self, ipc_to_bns):
        assert ipc_to_bns["474"]["new"] == "397"

    def test_ipc_475_kidnapping_begging(self, ipc_to_bns):
        assert ipc_to_bns["475"]["new"] == "398"

    def test_ipc_476_kidnapping_labour(self, ipc_to_bns):
        assert ipc_to_bns["476"]["new"] == "399"

    def test_ipc_477_kidnapping_marriage(self, ipc_to_bns):
        assert ipc_to_bns["477"]["new"] == "400"

    def test_ipc_478_kidnapping_deceit(self, ipc_to_bns):
        assert ipc_to_bns["478"]["new"] == "401"

    def test_ipc_479_abduction(self, ipc_to_bns):
        assert ipc_to_bns["479"]["new"] == "402"

    def test_ipc_480_abduction_punishment(self, ipc_to_bns):
        assert ipc_to_bns["480"]["new"] == "403"

    def test_ipc_481_abduction_begging(self, ipc_to_bns):
        assert ipc_to_bns["481"]["new"] == "404"

    def test_ipc_482_abduction_labour(self, ipc_to_bns):
        assert ipc_to_bns["482"]["new"] == "405"

    def test_ipc_483_abduction_marriage(self, ipc_to_bns):
        assert ipc_to_bns["483"]["new"] == "406"

    def test_ipc_484_abduction_servitude(self, ipc_to_bns):
        assert ipc_to_bns["484"]["new"] == "407"

    def test_ipc_485_trafficking(self, ipc_to_bns):
        assert ipc_to_bns["485"]["new"] == "408"

    def test_ipc_486_importing_woman(self, ipc_to_bns):
        assert ipc_to_bns["486"]["new"] == "409"

    def test_ipc_487_importing_child(self, ipc_to_bns):
        assert ipc_to_bns["487"]["new"] == "410"

    def test_ipc_488_selling_person(self, ipc_to_bns):
        assert ipc_to_bns["488"]["new"] == "411"

    def test_ipc_489_buying_person(self, ipc_to_bns):
        assert ipc_to_bns["489"]["new"] == "412"

    def test_ipc_490_unlawful_compulsion(self, ipc_to_bns):
        assert ipc_to_bns["490"]["new"] == "413"

    def test_ipc_491_habitual_trafficking(self, ipc_to_bns):
        assert ipc_to_bns["491"]["new"] == "414"

    def test_ipc_492_rape(self, ipc_to_bns):
        assert ipc_to_bns["492"]["new"] == "415"
        assert ipc_to_bns["492"]["name"] == "Rape"

    def test_ipc_493_rape_punishment(self, ipc_to_bns):
        assert ipc_to_bns["493"]["new"] == "416"

    def test_ipc_494_rape_minor(self, ipc_to_bns):
        assert ipc_to_bns["494"]["new"] == "417"

    def test_ipc_495_gang_rape(self, ipc_to_bns):
        assert ipc_to_bns["495"]["new"] == "418"

    def test_ipc_496_rape_public_servant(self, ipc_to_bns):
        assert ipc_to_bns["496"]["new"] == "419"

    def test_ipc_497_rape_armed_forces(self, ipc_to_bns):
        assert ipc_to_bns["497"]["new"] == "420"

    def test_ipc_498_rape_authority(self, ipc_to_bns):
        assert ipc_to_bns["498"]["new"] == "421"

    def test_ipc_501_defamation_publication(self, ipc_to_bns):
        assert ipc_to_bns["501"]["new"] == "358"

    def test_ipc_502_defamation_imputation(self, ipc_to_bns):
        assert ipc_to_bns["502"]["new"] == "359"

    def test_ipc_505_intimidation_anonymity(self, ipc_to_bns):
        assert ipc_to_bns["505"]["new"] == "362"

    def test_ipc_507_intimidation_letter(self, ipc_to_bns):
        assert ipc_to_bns["507"]["new"] == "364"

    def test_ipc_508_word_gesture(self, ipc_to_bns):
        assert ipc_to_bns["508"]["new"] == "365"

    def test_ipc_510_stalking(self, ipc_to_bns):
        assert ipc_to_bns["510"]["new"] == "367"

    def test_ipc_512_obscene_exposure(self, ipc_to_bns):
        assert ipc_to_bns["512"]["new"] == "369"


# ── Definition and Preamble Sections ─────────────────────────────


class TestDefinitionSections:
    def test_ipc_17_public_servant(self, ipc_to_bns):
        assert ipc_to_bns["17"]["new"] == "2"

    def test_ipc_21_good_faith(self, ipc_to_bns):
        assert ipc_to_bns["21"]["new"] == "2"

    def test_ipc_23_movable_property(self, ipc_to_bns):
        assert ipc_to_bns["23"]["new"] == "2"

    def test_ipc_25_wrongful_gain(self, ipc_to_bns):
        assert ipc_to_bns["25"]["new"] == "2"

    def test_ipc_26_dishonestly(self, ipc_to_bns):
        assert ipc_to_bns["26"]["new"] == "2"

    def test_ipc_27_fraudulently(self, ipc_to_bns):
        assert ipc_to_bns["27"]["new"] == "2"

    def test_ipc_28_reason_to_believe(self, ipc_to_bns):
        assert ipc_to_bns["28"]["new"] == "2"

    def test_ipc_29_document(self, ipc_to_bns):
        assert ipc_to_bns["29"]["new"] == "2"

    def test_ipc_30_valuable_security(self, ipc_to_bns):
        assert ipc_to_bns["30"]["new"] == "2"

    def test_ipc_40_life_legal_rights(self, ipc_to_bns):
        assert ipc_to_bns["40"]["new"] == "4"

    def test_ipc_43_force(self, ipc_to_bns):
        assert ipc_to_bns["43"]["new"] == "5"

    def test_ipc_44_injury(self, ipc_to_bns):
        assert ipc_to_bns["44"]["new"] == "6"

    def test_ipc_45_life_limb_health(self, ipc_to_bns):
        assert ipc_to_bns["45"]["new"] == "7"

    def test_ipc_46_death(self, ipc_to_bns):
        assert ipc_to_bns["46"]["new"] == "8"

    def test_ipc_47_woman_child(self, ipc_to_bns):
        assert ipc_to_bns["47"]["new"] == "8"

    def test_ipc_49_measure_punishment(self, ipc_to_bns):
        assert ipc_to_bns["49"]["new"] == "9"

    def test_ipc_50_expression_term(self, ipc_to_bns):
        assert ipc_to_bns["50"]["new"] == "10"

    def test_ipc_51_gender_number(self, ipc_to_bns):
        assert ipc_to_bns["51"]["new"] == "11"

    def test_ipc_52_good_faith(self, ipc_to_bns):
        assert ipc_to_bns["52"]["new"] == "12"

    def test_ipc_52a_harvested_crops(self, ipc_to_bns):
        assert ipc_to_bns["52A"]["new"] == "12"


# ── Joint Liability Sections ─────────────────────────────────────


class TestJointLiability:
    def test_ipc_34_acts_several_persons(self, ipc_to_bns):
        assert ipc_to_bns["34"]["new"] == "3"

    def test_ipc_35_committal_several(self, ipc_to_bns):
        assert ipc_to_bns["35"]["new"] == "3"

    def test_ipc_36_offence_person_bound(self, ipc_to_bns):
        assert ipc_to_bns["36"]["new"] == "3"

    def test_ipc_37_offence_member_assembly(self, ipc_to_bns):
        assert ipc_to_bns["37"]["new"] == "3"

    def test_ipc_38_act_coercion(self, ipc_to_bns):
        assert ipc_to_bns["38"]["new"] == "3"

    def test_ipc_39_person_causing_effect(self, ipc_to_bns):
        assert ipc_to_bns["39"]["new"] == "3"


# ── Punishment and Sentence Sections ─────────────────────────────


class TestPunishmentSections:
    def test_ipc_53_punishments(self, ipc_to_bns):
        assert ipc_to_bns["53"]["new"] == "61"

    def test_ipc_53a_attempt_punishment(self, ipc_to_bns):
        assert ipc_to_bns["53A"]["new"] == "62"

    def test_ipc_54_commutation_death(self, ipc_to_bns):
        assert ipc_to_bns["54"]["new"] == "63"

    def test_ipc_55_commutation_life(self, ipc_to_bns):
        assert ipc_to_bns["55"]["new"] == "64"

    def test_ipc_55a_calculation_sentence(self, ipc_to_bns):
        assert ipc_to_bns["55A"]["new"] == "65"

    def test_ipc_56_forfeiture_property(self, ipc_to_bns):
        assert ipc_to_bns["56"]["new"] == "66"

    def test_ipc_57_fine_payment(self, ipc_to_bns):
        assert ipc_to_bns["57"]["new"] == "67"

    def test_ipc_58_fine_limits(self, ipc_to_bns):
        assert ipc_to_bns["58"]["new"] == "68"

    def test_ipc_59_fine_proportional(self, ipc_to_bns):
        assert ipc_to_bns["59"]["new"] == "69"

    def test_ipc_60_sentence_cumulative(self, ipc_to_bns):
        assert ipc_to_bns["60"]["new"] == "70"

    def test_ipc_62_security_good_behavior(self, ipc_to_bns):
        assert ipc_to_bns["62"]["new"] == "71"

    def test_ipc_66_previous_conviction(self, ipc_to_bns):
        assert ipc_to_bns["66"]["new"] == "75"


# ── Abetment and Conspiracy Sections ─────────────────────────────


class TestAbetmentSections:
    def test_ipc_107_abetment_base(self, ipc_to_bns):
        assert ipc_to_bns["107"]["new"] == "116"

    def test_ipc_108_abettor_present(self, ipc_to_bns):
        assert ipc_to_bns["108"]["new"] == "117"

    def test_ipc_108a_abetment_commit(self, ipc_to_bns):
        assert ipc_to_bns["108A"]["new"] == "118"

    def test_ipc_109_abetment_punishment(self, ipc_to_bns):
        assert ipc_to_bns["109"]["new"] == "119"

    def test_ipc_110_abetting_punishment(self, ipc_to_bns):
        assert ipc_to_bns["110"]["new"] == "120"

    def test_ipc_111_abettor_act_different(self, ipc_to_bns):
        assert ipc_to_bns["111"]["new"] == "121"

    def test_ipc_112_abetment_wage_war(self, ipc_to_bns):
        assert ipc_to_bns["112"]["new"] == "122"

    def test_ipc_113_abettor_war(self, ipc_to_bns):
        assert ipc_to_bns["113"]["new"] == "123"

    def test_ipc_114_abettor_present_offence(self, ipc_to_bns):
        assert ipc_to_bns["114"]["new"] == "124"

    def test_ipc_115_abetment_offence_capital(self, ipc_to_bns):
        assert ipc_to_bns["115"]["new"] == "125"

    def test_ipc_116_abetment_offence_imprisonment(self, ipc_to_bns):
        assert ipc_to_bns["116"]["new"] == "126"

    def test_ipc_117_abetting_commission(self, ipc_to_bns):
        assert ipc_to_bns["117"]["new"] == "127"

    def test_ipc_118_concealing_design(self, ipc_to_bns):
        assert ipc_to_bns["118"]["new"] == "128"

    def test_ipc_119_public_servant_concealing(self, ipc_to_bns):
        assert ipc_to_bns["119"]["new"] == "129"

    def test_ipc_120_concealment_agent(self, ipc_to_bns):
        assert ipc_to_bns["120"]["new"] == "130"


# ── Offences Against State Sections ──────────────────────────────


class TestOffencesAgainstState:
    def test_ipc_121_waging_war(self, ipc_to_bns):
        assert ipc_to_bns["121"]["new"] == "133"

    def test_ipc_121a_conspiracy_war(self, ipc_to_bns):
        assert ipc_to_bns["121A"]["new"] == "134"

    def test_ipc_122_collecting_arms(self, ipc_to_bns):
        assert ipc_to_bns["122"]["new"] == "135"

    def test_ipc_123_concealing_treasure(self, ipc_to_bns):
        assert ipc_to_bns["123"]["new"] == "136"

    def test_ipc_124_assaulting_president(self, ipc_to_bns):
        assert ipc_to_bns["124"]["new"] == "137"

    def test_ipc_124a_sedition(self, ipc_to_bns):
        assert ipc_to_bns["124A"]["new"] == "138"

    def test_ipc_125_waging_war_tribal(self, ipc_to_bns):
        assert ipc_to_bns["125"]["new"] == "139"

    def test_ipc_126_piracy(self, ipc_to_bns):
        assert ipc_to_bns["126"]["new"] == "140"


# ── Kidnapping and Trafficking Sections ──────────────────────────


class TestKidnappingSections:
    def test_ipc_254_kidnapping_base(self, ipc_to_bns):
        assert ipc_to_bns["254"]["new"] == "268"
        assert ipc_to_bns["254"]["name"] == "Kidnapping"

    def test_ipc_255_kidnapping_india(self, ipc_to_bns):
        assert ipc_to_bns["255"]["new"] == "269"

    def test_ipc_256_kidnapping_begging(self, ipc_to_bns):
        assert ipc_to_bns["256"]["new"] == "270"

    def test_ipc_257_kidnapping_labour(self, ipc_to_bns):
        assert ipc_to_bns["257"]["new"] == "271"

    def test_ipc_258_kidnapping_marriage(self, ipc_to_bns):
        assert ipc_to_bns["258"]["new"] == "272"

    def test_ipc_259_kidnapping_deceit(self, ipc_to_bns):
        assert ipc_to_bns["259"]["new"] == "273"

    def test_ipc_260_abduction(self, ipc_to_bns):
        assert ipc_to_bns["260"]["new"] == "274"
        assert ipc_to_bns["260"]["name"] == "Abduction"

    def test_ipc_261_trafficking(self, ipc_to_bns):
        assert ipc_to_bns["261"]["new"] == "275"

    def test_ipc_262_importation_person(self, ipc_to_bns):
        assert ipc_to_bns["262"]["new"] == "276"

    def test_ipc_263_selling_person(self, ipc_to_bns):
        assert ipc_to_bns["263"]["new"] == "277"

    def test_ipc_264_buying_person(self, ipc_to_bns):
        assert ipc_to_bns["264"]["new"] == "278"


# ── Property Offences ────────────────────────────────────────────


class TestPropertyOffences:
    def test_ipc_266_theft_base(self, ipc_to_bns):
        assert ipc_to_bns["266"]["new"] == "280"
        assert ipc_to_bns["266"]["name"] == "Theft"

    def test_ipc_267_extortion_base(self, ipc_to_bns):
        assert ipc_to_bns["267"]["new"] == "281"

    def test_ipc_268_robbery_base(self, ipc_to_bns):
        assert ipc_to_bns["268"]["new"] == "282"

    def test_ipc_269_dacoity_base(self, ipc_to_bns):
        assert ipc_to_bns["269"]["new"] == "283"

    def test_ipc_270_criminal_misappropriation(self, ipc_to_bns):
        assert ipc_to_bns["270"]["new"] == "284"

    def test_ipc_271_criminal_breach_trust(self, ipc_to_bns):
        assert ipc_to_bns["271"]["new"] == "285"

    def test_ipc_272_receiving_stolen(self, ipc_to_bns):
        assert ipc_to_bns["272"]["new"] == "286"

    def test_ipc_273_cheating(self, ipc_to_bns):
        assert ipc_to_bns["273"]["new"] == "287"

    def test_ipc_274_cheating_personation(self, ipc_to_bns):
        assert ipc_to_bns["274"]["new"] == "288"

    def test_ipc_275_fraudulent_execution(self, ipc_to_bns):
        assert ipc_to_bns["275"]["new"] == "289"

    def test_ipc_276_fraudulent_concealment(self, ipc_to_bns):
        assert ipc_to_bns["276"]["new"] == "290"

    def test_ipc_277_mischief(self, ipc_to_bns):
        assert ipc_to_bns["277"]["new"] == "291"

    def test_ipc_278_mischief_fire(self, ipc_to_bns):
        assert ipc_to_bns["278"]["new"] == "292"

    def test_ipc_279_mischief_explosive(self, ipc_to_bns):
        assert ipc_to_bns["279"]["new"] == "293"

    def test_ipc_280_mischief_causes_damage(self, ipc_to_bns):
        assert ipc_to_bns["280"]["new"] == "294"

    def test_ipc_281_mischief_animals(self, ipc_to_bns):
        assert ipc_to_bns["281"]["new"] == "295"

    def test_ipc_282_mischief_killing_animal(self, ipc_to_bns):
        assert ipc_to_bns["282"]["new"] == "296"

    def test_ipc_283_mischief_poisoning(self, ipc_to_bns):
        assert ipc_to_bns["283"]["new"] == "297"

    def test_ipc_284_mischief_traps(self, ipc_to_bns):
        assert ipc_to_bns["284"]["new"] == "298"

    def test_ipc_285_criminal_trespass_base(self, ipc_to_bns):
        assert ipc_to_bns["285"]["new"] == "299"

    def test_ipc_286_house_trespass(self, ipc_to_bns):
        assert ipc_to_bns["286"]["new"] == "300"

    def test_ipc_287_lurking_house_trespass(self, ipc_to_bns):
        assert ipc_to_bns["287"]["new"] == "301"

    def test_ipc_288_house_breaking_night(self, ipc_to_bns):
        assert ipc_to_bns["288"]["new"] == "302"

    def test_ipc_289_return_house(self, ipc_to_bns):
        assert ipc_to_bns["289"]["new"] == "303"

    def test_ipc_290_entry_good_faith(self, ipc_to_bns):
        assert ipc_to_bns["290"]["new"] == "304"

    def test_ipc_291_door_broken(self, ipc_to_bns):
        assert ipc_to_bns["291"]["new"] == "305"

    def test_ipc_292_forcible_entry(self, ipc_to_bns):
        assert ipc_to_bns["292"]["new"] == "306"

    def test_ipc_293_disguised_entry(self, ipc_to_bns):
        assert ipc_to_bns["293"]["new"] == "307"

    def test_ipc_294_entrance_criminal_intent(self, ipc_to_bns):
        assert ipc_to_bns["294"]["new"] == "308"

    def test_ipc_295_remaining_enclosed(self, ipc_to_bns):
        assert ipc_to_bns["295"]["new"] == "309"

    def test_ipc_296_compelling_attendance(self, ipc_to_bns):
        assert ipc_to_bns["296"]["new"] == "310"

    def test_ipc_297_violation_order(self, ipc_to_bns):
        assert ipc_to_bns["297"]["new"] == "311"

    def test_ipc_298_violation_compromise(self, ipc_to_bns):
        assert ipc_to_bns["298"]["new"] == "312"


# ── Public Nuisance Sections ─────────────────────────────────────


class TestPublicNuisance:
    def test_ipc_371_public_nuisance(self, ipc_to_bns):
        assert ipc_to_bns["371"]["new"] == "173"

    def test_ipc_372_nuisance_public_servant(self, ipc_to_bns):
        assert ipc_to_bns["372"]["new"] == "174"

    def test_ipc_373_offensive_smell(self, ipc_to_bns):
        assert ipc_to_bns["373"]["new"] == "175"

    def test_ipc_374_offensive_trade(self, ipc_to_bns):
        assert ipc_to_bns["374"]["new"] == "176"

    def test_ipc_375_punishment_nuisance(self, ipc_to_bns):
        assert ipc_to_bns["375"]["new"] == "177"

    def test_ipc_376_obscene_exposure(self, ipc_to_bns):
        assert ipc_to_bns["376"]["new"] == "178"

    def test_ipc_377_obscene_act(self, ipc_to_bns):
        assert ipc_to_bns["377"]["new"] == "179"


# ── IPC 312-329 Child-Related Sections ───────────────────────────


class TestChildRelatedSections:
    def test_ipc_312_woman_miscarriage(self, ipc_to_bns):
        assert ipc_to_bns["312"]["new"] == "114"

    def test_ipc_313_child_not_born_alive(self, ipc_to_bns):
        assert ipc_to_bns["313"]["new"] == "115"

    def test_ipc_314_quick_child(self, ipc_to_bns):
        assert ipc_to_bns["314"]["new"] == "116"

    def test_ipc_315_death_quick_child(self, ipc_to_bns):
        assert ipc_to_bns["315"]["new"] == "117"

    def test_ipc_316_exposing_child(self, ipc_to_bns):
        assert ipc_to_bns["316"]["new"] == "118"

    def test_ipc_317_deserting_child(self, ipc_to_bns):
        assert ipc_to_bns["317"]["new"] == "119"

    def test_ipc_318_child_found(self, ipc_to_bns):
        assert ipc_to_bns["318"]["new"] == "120"

    def test_ipc_319_kidnapping_child(self, ipc_to_bns):
        assert ipc_to_bns["319"]["new"] == "121"

    def test_ipc_320_buying_selling_child(self, ipc_to_bns):
        assert ipc_to_bns["320"]["new"] == "122"

    def test_ipc_321_kidnapping_child_begging(self, ipc_to_bns):
        assert ipc_to_bns["321"]["new"] == "123"

    def test_ipc_322_kidnapping_child_labour(self, ipc_to_bns):
        assert ipc_to_bns["322"]["new"] == "124"

    def test_ipc_323_exposing_child_streets(self, ipc_to_bns):
        assert ipc_to_bns["323"]["new"] == "125"

    def test_ipc_324_omission_report(self, ipc_to_bns):
        assert ipc_to_bns["324"]["new"] == "126"

    def test_ipc_325_child_found_concealing(self, ipc_to_bns):
        assert ipc_to_bns["325"]["new"] == "127"

    def test_ipc_326_procuring_child(self, ipc_to_bns):
        assert ipc_to_bns["326"]["new"] == "128"

    def test_ipc_327_using_child_begging(self, ipc_to_bns):
        assert ipc_to_bns["327"]["new"] == "129"

    def test_ipc_328_controlling_child_beggar(self, ipc_to_bns):
        assert ipc_to_bns["328"]["new"] == "130"

    def test_ipc_329_habitual_offender(self, ipc_to_bns):
        assert ipc_to_bns["329"]["new"] == "131"


# ── Reverse Mapping Consistency ──────────────────────────────────


class TestReverseMappingConsistency:
    def test_reverse_101_maps_to_302(self, bns_to_ipc):
        assert bns_to_ipc["101"]["old"] == "302"
        assert bns_to_ipc["101"]["name"] == "Murder"

    def test_reverse_102_maps_to_303(self, bns_to_ipc):
        assert bns_to_ipc["102"]["old"] == "303"
        assert bns_to_ipc["102"]["name"] == "Culpable Homicide"

    def test_reverse_103_maps_to_304(self, bns_to_ipc):
        assert bns_to_ipc["103"]["old"] == "304"
        assert bns_to_ipc["103"]["name"] == "Death by Negligence"

    def test_reverse_104_maps_to_304a(self, bns_to_ipc):
        assert bns_to_ipc["104"]["old"] == "304A"

    def test_reverse_105_maps_to_304b(self, bns_to_ipc):
        assert bns_to_ipc["105"]["old"] == "304B"

    def test_reverse_106_maps_to_305(self, bns_to_ipc):
        assert bns_to_ipc["106"]["old"] == "305"

    def test_reverse_107_maps_to_306(self, bns_to_ipc):
        assert bns_to_ipc["107"]["old"] == "306"

    def test_reverse_109_maps_to_307(self, bns_to_ipc):
        assert bns_to_ipc["109"]["old"] == "307"

    def test_reverse_110_maps_to_308(self, bns_to_ipc):
        assert bns_to_ipc["110"]["old"] == "308"

    def test_reverse_111_maps_to_309(self, bns_to_ipc):
        assert bns_to_ipc["111"]["old"] == "309"

    def test_reverse_112_maps_to_310(self, bns_to_ipc):
        assert bns_to_ipc["112"]["old"] == "310"

    def test_reverse_113_maps_to_311(self, bns_to_ipc):
        assert bns_to_ipc["113"]["old"] == "311"

    def test_reverse_303_maps_to_378(self, bns_to_ipc):
        assert bns_to_ipc["303"]["old"] == "378"
        assert bns_to_ipc["303"]["name"] == "Theft"

    def test_reverse_318_maps_to_420(self, bns_to_ipc):
        assert bns_to_ipc["318"]["old"] == "420"
        assert bns_to_ipc["318"]["name"] == "Cheating"

    def test_reverse_356_maps_to_499(self, bns_to_ipc):
        assert bns_to_ipc["356"]["old"] == "499"
        assert bns_to_ipc["356"]["name"] == "Defamation"


# ── Bidirectional Consistency ────────────────────────────────────


class TestBidirectionalConsistency:
    def test_reverse_forward_consistent(self, ipc_to_bns, bns_to_ipc):
        for bns_sec, data in bns_to_ipc.items():
            ipc_sec = data["old"]
            assert ipc_sec in ipc_to_bns, (
                f"BNS {bns_sec} -> IPC {ipc_sec} but IPC {ipc_sec} not in forward map"
            )
            assert ipc_to_bns[ipc_sec]["new"] == bns_sec, (
                f"BNS {bns_sec} -> IPC {ipc_sec} but "
                f"IPC {ipc_sec} -> BNS "
                f"{ipc_to_bns[ipc_sec]['new']}"
            )

    def test_reverse_entries_are_canonical(self, ipc_to_bns, bns_to_ipc):
        for bns_sec, data in bns_to_ipc.items():
            ipc_sec = data["old"]
            fwd_data = ipc_to_bns[ipc_sec]
            assert fwd_data["new"] == bns_sec

    def test_many_to_one_handled(self, ipc_to_bns):
        seen = {}
        for ipc_sec, data in ipc_to_bns.items():
            bns_sec = data["new"]
            if bns_sec in seen:
                prev = seen[bns_sec]
                assert data["name"] != ipc_to_bns[prev]["name"], (
                    f"Duplicate BNS {bns_sec} from IPC "
                    f"{prev} and {ipc_sec} with same name"
                )
            seen[bns_sec] = ipc_sec


# ── No Circular References ──────────────────────────────────────


class TestNoCircularReferences:
    def test_no_circular_in_forward(self, ipc_to_bns):
        visited = set()
        for ipc_sec in ipc_to_bns:
            assert ipc_sec not in visited, f"Circular reference at IPC {ipc_sec}"
            visited.add(ipc_sec)

    def test_no_circular_in_reverse(self, bns_to_ipc):
        visited = set()
        for bns_sec in bns_to_ipc:
            assert bns_sec not in visited, f"Circular reference at BNS {bns_sec}"
            visited.add(bns_sec)


# ── BNS Section Number Validation ───────────────────────────────


class TestBnsSectionNumberValidation:
    VALID_BNS_PATTERN = re.compile(r"^\d+[A-Z]?$")

    def test_all_new_values_are_valid_bns(self, ipc_to_bns):
        invalid = []
        for ipc_sec, data in ipc_to_bns.items():
            new_val = data["new"]
            if not self.VALID_BNS_PATTERN.match(str(new_val)):
                invalid.append(f"IPC {ipc_sec}: {new_val}")
        if invalid:
            pytest.fail("Invalid BNS section numbers:\n" + "\n".join(invalid[:20]))

    def test_all_old_values_are_valid_ipc(self, ipc_to_bns):
        invalid = []
        for ipc_sec, data in ipc_to_bns.items():
            if not self.VALID_BNS_PATTERN.match(str(ipc_sec)):
                invalid.append(f"Invalid IPC key: {ipc_sec}")
        if invalid:
            pytest.fail("Invalid IPC section keys:\n" + "\n".join(invalid[:20]))

    def test_reverse_old_values_are_valid_ipc(self, bns_to_ipc):
        invalid = []
        for bns_sec, data in bns_to_ipc.items():
            old_val = data["old"]
            if not self.VALID_BNS_PATTERN.match(str(old_val)):
                invalid.append(f"BNS {bns_sec}: {old_val}")
        if invalid:
            pytest.fail("Invalid IPC values in reverse:\n" + "\n".join(invalid[:20]))

    def test_reverse_bns_keys_are_numeric(self, bns_to_ipc):
        for bns_sec in bns_to_ipc:
            assert bns_sec.isdigit(), f"Non-numeric BNS key: {bns_sec}"


# ── Edge Cases ──────────────────────────────────────────────────


class TestEdgeCases:
    def test_section_with_letter_suffix_304a(self, ipc_to_bns):
        assert "304A" in ipc_to_bns
        assert ipc_to_bns["304A"]["new"] == "104"

    def test_section_with_letter_suffix_304b(self, ipc_to_bns):
        assert "304B" in ipc_to_bns
        assert ipc_to_bns["304B"]["new"] == "105"

    def test_section_with_letter_suffix_120a(self, ipc_to_bns):
        assert "120A" in ipc_to_bns
        assert ipc_to_bns["120A"]["new"] == "131"

    def test_section_with_letter_suffix_120b(self, ipc_to_bns):
        assert "120B" in ipc_to_bns
        assert ipc_to_bns["120B"]["new"] == "132"

    def test_section_with_letter_suffix_121a(self, ipc_to_bns):
        assert "121A" in ipc_to_bns
        assert ipc_to_bns["121A"]["new"] == "134"

    def test_section_with_letter_suffix_124a(self, ipc_to_bns):
        assert "124A" in ipc_to_bns
        assert ipc_to_bns["124A"]["new"] == "138"

    def test_section_with_letter_suffix_108a(self, ipc_to_bns):
        assert "108A" in ipc_to_bns
        assert ipc_to_bns["108A"]["new"] == "118"

    def test_high_section_number_511(self, ipc_to_bns):
        assert "511" in ipc_to_bns
        assert ipc_to_bns["511"]["new"] == "368"

    def test_high_section_number_512(self, ipc_to_bns):
        assert "512" in ipc_to_bns
        assert ipc_to_bns["512"]["new"] == "369"

    def test_low_section_number_14(self, ipc_to_bns):
        assert "14" in ipc_to_bns
        assert ipc_to_bns["14"]["new"] == "2"

    def test_empty_mapping_entry_skipped(self, ipc_to_bns):
        for sec, data in ipc_to_bns.items():
            assert data["new"] != "", f"IPC {sec} has empty 'new' value"

    def test_no_none_values_in_mapping(self, ipc_to_bns):
        for sec, data in ipc_to_bns.items():
            assert data["new"] is not None, f"IPC {sec} has None 'new' value"
            assert data["name"] is not None, f"IPC {sec} has None 'name' value"

    def test_many_to_one_sections_share_bns(self, ipc_to_bns):
        bns_groups = {}
        for ipc_sec, data in ipc_to_bns.items():
            bns_sec = data["new"]
            bns_groups.setdefault(bns_sec, []).append(ipc_sec)
        for bns_sec, ipc_list in bns_groups.items():
            assert len(ipc_list) >= 1


# ── Router Integration Tests ─────────────────────────────────────


class TestRouterIntegration:
    def test_router_legal_map_loads(self, router):
        assert isinstance(router.legal_map, dict)
        assert len(router.legal_map) >= 485

    def test_router_legal_map_matches_json(self, router, ipc_to_bns):
        assert router.legal_map.keys() == ipc_to_bns.keys()

    def test_router_legal_map_302(self, router):
        assert router.legal_map["302"]["new"] == "101"
        assert router.legal_map["302"]["name"] == "Murder"

    def test_router_legal_map_420(self, router):
        assert router.legal_map["420"]["new"] == "318"

    def test_router_legal_map_379(self, router):
        assert router.legal_map["379"]["new"] == "304"

    def test_router_legal_map_376(self, router):
        assert router.legal_map["376"]["new"] == "178"

    def test_router_legal_map_304(self, router):
        assert router.legal_map["304"]["new"] == "103"

    def test_router_legal_map_304a(self, router):
        assert router.legal_map["304A"]["new"] == "104"

    def test_router_legal_map_304b(self, router):
        assert router.legal_map["304B"]["new"] == "105"

    def test_router_legal_map_all_entries_have_new(self, router):
        for sec, data in router.legal_map.items():
            assert "new" in data
            assert data["new"]

    def test_router_legal_map_all_entries_have_name(self, router):
        for sec, data in router.legal_map.items():
            assert "name" in data
            assert data["name"]

    def test_router_legal_map_is_same_content(self, router, ipc_to_bns):
        assert router.legal_map == ipc_to_bns

    def test_router_normalize_adds_bns_section(self, router):
        query, mappings = router.normalize_query("What is IPC Section 302")
        assert "BNS" in query.upper()
        assert len(mappings) > 0

    def test_router_normalize_multiple_sections(self, router):
        query, mappings = router.normalize_query("Explain IPC 302 and IPC 379")
        assert len(mappings) >= 2


# ── Mapping Completeness Tests ──────────────────────────────────


class TestMappingCompleteness:
    def test_major_ipc_sections_present(self, ipc_to_bns):
        required = [
            "302",
            "303",
            "304",
            "304A",
            "304B",
            "305",
            "306",
            "307",
            "308",
            "309",
            "376",
            "378",
            "379",
            "380",
            "381",
            "382",
            "383",
            "384",
            "385",
            "386",
            "387",
            "388",
            "389",
            "390",
            "391",
            "392",
            "393",
            "394",
            "395",
            "396",
            "397",
            "398",
            "399",
            "400",
            "401",
            "402",
            "403",
            "404",
            "405",
            "406",
            "407",
            "408",
            "409",
            "410",
            "411",
            "412",
            "413",
            "414",
            "415",
            "416",
            "417",
            "418",
            "419",
            "420",
            "421",
            "422",
            "423",
            "424",
            "425",
            "426",
            "427",
            "428",
            "429",
            "430",
            "431",
            "432",
            "433",
            "434",
            "435",
            "436",
            "437",
            "438",
            "439",
            "440",
            "441",
            "442",
            "443",
            "444",
            "445",
            "446",
            "447",
            "448",
            "449",
            "450",
            "451",
            "452",
            "453",
            "454",
            "455",
            "456",
            "457",
            "458",
            "459",
            "460",
            "461",
            "462",
            "463",
            "464",
            "465",
            "466",
            "467",
            "468",
            "469",
            "470",
            "471",
            "472",
            "473",
            "474",
            "475",
            "476",
            "477",
            "478",
            "479",
            "480",
            "481",
            "482",
            "483",
            "484",
            "485",
            "486",
            "487",
            "488",
            "489",
            "490",
            "491",
            "492",
            "493",
            "494",
            "495",
            "496",
            "497",
            "498",
            "499",
            "500",
            "501",
            "502",
            "503",
            "504",
            "505",
            "506",
            "507",
            "508",
            "509",
            "510",
            "511",
        ]
        missing = [s for s in required if s not in ipc_to_bns]
        assert not missing, f"Missing required sections: {missing}"

    def test_definition_sections_present(self, ipc_to_bns):
        defs = [
            "14",
            "17",
            "21",
            "23",
            "25",
            "26",
            "27",
            "28",
            "29",
            "30",
            "34",
            "35",
            "36",
            "37",
            "38",
            "39",
            "40",
            "43",
            "44",
            "45",
            "46",
            "47",
            "49",
            "50",
            "51",
            "52",
        ]
        missing = [s for s in defs if s not in ipc_to_bns]
        assert not missing, f"Missing definition sections: {missing}"

    def test_punishment_sections_present(self, ipc_to_bns):
        punish = [
            "53",
            "53A",
            "54",
            "55",
            "55A",
            "56",
            "57",
            "58",
            "59",
            "60",
        ]
        missing = [s for s in punish if s not in ipc_to_bns]
        assert not missing, f"Missing punishment sections: {missing}"

    def testabetment_sections_present(self, ipc_to_bns):
        abet = [
            "107",
            "108",
            "108A",
            "109",
            "110",
            "111",
            "112",
            "113",
            "114",
            "115",
            "116",
            "117",
            "118",
            "119",
            "120",
            "120A",
            "120B",
        ]
        missing = [s for s in abet if s not in ipc_to_bns]
        assert not missing, f"Missing abetment sections: {missing}"

    def test_kidnapping_sections_present(self, ipc_to_bns):
        kidnap = [
            "254",
            "255",
            "256",
            "257",
            "258",
            "259",
            "260",
            "261",
            "262",
            "263",
            "264",
            "265",
        ]
        missing = [s for s in kidnap if s not in ipc_to_bns]
        assert not missing, f"Missing kidnapping sections: {missing}"

    def test_property_sections_present(self, ipc_to_bns):
        prop = [
            "266",
            "267",
            "268",
            "269",
            "270",
            "271",
            "272",
            "273",
            "274",
            "275",
            "276",
            "277",
            "278",
            "279",
            "280",
        ]
        missing = [s for s in prop if s not in ipc_to_bns]
        assert not missing, f"Missing property sections: {missing}"


# ── Additional Assertion Coverage ───────────────────────────────


class TestAdditionalCoverage:
    def test_ipc_67_chapter_notes(self, ipc_to_bns):
        assert ipc_to_bns["67"]["new"] == "76"

    def test_ipc_68_executive_functionaries(self, ipc_to_bns):
        assert ipc_to_bns["68"]["new"] == "77"

    def test_ipc_69_offences_against_state(self, ipc_to_bns):
        assert ipc_to_bns["69"]["new"] == "78"

    def test_ipc_70_word_or_sign(self, ipc_to_bns):
        assert ipc_to_bns["70"]["new"] == "79"

    def test_ipc_71_judge_court(self, ipc_to_bns):
        assert ipc_to_bns["71"]["new"] == "80"

    def test_ipc_72_everything_official(self, ipc_to_bns):
        assert ipc_to_bns["72"]["new"] == "81"

    def test_ipc_73_judge_acting_judicially(self, ipc_to_bns):
        assert ipc_to_bns["73"]["new"] == "82"

    def test_ipc_74_person_discharging_duties(self, ipc_to_bns):
        assert ipc_to_bns["74"]["new"] == "83"

    def test_ipc_75_medical_practitioner(self, ipc_to_bns):
        assert ipc_to_bns["75"]["new"] == "84"

    def test_ipc_76_illegal_oath(self, ipc_to_bns):
        assert ipc_to_bns["76"]["new"] == "85"

    def test_ipc_77_act_good_faith(self, ipc_to_bns):
        assert ipc_to_bns["77"]["new"] == "86"

    def test_ipc_78_communication_marriage(self, ipc_to_bns):
        assert ipc_to_bns["78"]["new"] == "87"

    def test_ipc_79_trivial_error(self, ipc_to_bns):
        assert ipc_to_bns["79"]["new"] == "88"

    def test_ipc_80_accident_exercise_right(self, ipc_to_bns):
        assert ipc_to_bns["80"]["new"] == "89"

    def test_ipc_81_sleep_intoxication(self, ipc_to_bns):
        assert ipc_to_bns["81"]["new"] == "90"

    def test_ipc_83_child_7_12(self, ipc_to_bns):
        assert ipc_to_bns["83"]["new"] == "92"

    def test_ipc_85_intoxication_no_consent(self, ipc_to_bns):
        assert ipc_to_bns["85"]["new"] == "94"

    def test_ipc_86_act_slight_harm(self, ipc_to_bns):
        assert ipc_to_bns["86"]["new"] == "95"

    def test_ipc_88_right_body_defense(self, ipc_to_bns):
        assert ipc_to_bns["88"]["new"] == "97"

    def test_ipc_89_right_against_animal(self, ipc_to_bns):
        assert ipc_to_bns["89"]["new"] == "98"

    def test_ipc_90_right_illegal_assault(self, ipc_to_bns):
        assert ipc_to_bns["90"]["new"] == "99"

    def test_ipc_91_right_cause_death(self, ipc_to_bns):
        assert ipc_to_bns["91"]["new"] == "100"

    def test_ipc_93_right_rape(self, ipc_to_bns):
        assert ipc_to_bns["93"]["new"] == "102"

    def test_ipc_94_right_kidnapping(self, ipc_to_bns):
        assert ipc_to_bns["94"]["new"] == "103"

    def test_ipc_95_right_thefts(self, ipc_to_bns):
        assert ipc_to_bns["95"]["new"] == "104"

    def test_ipc_96_right_limit(self, ipc_to_bns):
        assert ipc_to_bns["96"]["new"] == "105"

    def test_ipc_97_right_theft_case(self, ipc_to_bns):
        assert ipc_to_bns["97"]["new"] == "106"

    def test_ipc_98_right_trespass(self, ipc_to_bns):
        assert ipc_to_bns["98"]["new"] == "107"

    def test_ipc_99_right_abates(self, ipc_to_bns):
        assert ipc_to_bns["99"]["new"] == "108"

    def test_ipc_101_right_disappears(self, ipc_to_bns):
        assert ipc_to_bns["101"]["new"] == "110"

    def test_ipc_102_right_starts(self, ipc_to_bns):
        assert ipc_to_bns["102"]["new"] == "111"

    def test_ipc_103_right_after_attempt(self, ipc_to_bns):
        assert ipc_to_bns["103"]["new"] == "112"

    def test_ipc_104_right_use_force(self, ipc_to_bns):
        assert ipc_to_bns["104"]["new"] == "113"

    def test_ipc_105_right_abettor(self, ipc_to_bns):
        assert ipc_to_bns["105"]["new"] == "114"

    def test_ipc_106_right_assault(self, ipc_to_bns):
        assert ipc_to_bns["106"]["new"] == "115"

    def test_ipc_127_affray(self, ipc_to_bns):
        assert ipc_to_bns["127"]["new"] == "141"

    def test_ipc_128_assaulting_public_servant(self, ipc_to_bns):
        assert ipc_to_bns["128"]["new"] == "142"

    def test_ipc_129_violent_crime(self, ipc_to_bns):
        assert ipc_to_bns["129"]["new"] == "143"

    def test_ipc_130_joining_unlawful(self, ipc_to_bns):
        assert ipc_to_bns["130"]["new"] == "144"

    def test_ipc_131_being_member(self, ipc_to_bns):
        assert ipc_to_bns["131"]["new"] == "145"

    def test_ipc_132_knowingly_joining(self, ipc_to_bns):
        assert ipc_to_bns["132"]["new"] == "146"

    def test_ipc_133_rioting(self, ipc_to_bns):
        assert ipc_to_bns["133"]["new"] == "147"

    def test_ipc_134_rioting_weapon(self, ipc_to_bns):
        assert ipc_to_bns["134"]["new"] == "148"

    def test_ipc_135_every_member_liable(self, ipc_to_bns):
        assert ipc_to_bns["135"]["new"] == "149"

    def test_ipc_136_hiring_riot(self, ipc_to_bns):
        assert ipc_to_bns["136"]["new"] == "150"

    def test_ipc_137_affray_public(self, ipc_to_bns):
        assert ipc_to_bns["137"]["new"] == "151"

    def test_ipc_138_assault_president(self, ipc_to_bns):
        assert ipc_to_bns["138"]["new"] == "152"

    def test_ipc_139_harboring_servant(self, ipc_to_bns):
        assert ipc_to_bns["139"]["new"] == "153"

    def test_ipc_140_false_statement(self, ipc_to_bns):
        assert ipc_to_bns["140"]["new"] == "154"

    def test_ipc_141_servant_disobeying(self, ipc_to_bns):
        assert ipc_to_bns["141"]["new"] == "155"

    def test_ipc_142_misconduct_servant(self, ipc_to_bns):
        assert ipc_to_bns["142"]["new"] == "156"

    def test_ipc_143_servant_bribery(self, ipc_to_bns):
        assert ipc_to_bns["143"]["new"] == "157"

    def test_ipc_144_criminal_intimidation(self, ipc_to_bns):
        assert ipc_to_bns["144"]["new"] == "158"

    def test_ipc_145_intimidation_death(self, ipc_to_bns):
        assert ipc_to_bns["145"]["new"] == "159"

    def test_ipc_146_uttering_words(self, ipc_to_bns):
        assert ipc_to_bns["146"]["new"] == "160"

    def test_ipc_147_defamation(self, ipc_to_bns):
        assert ipc_to_bns["147"]["new"] == "161"

    def test_ipc_148_printing_defamatory(self, ipc_to_bns):
        assert ipc_to_bns["148"]["new"] == "162"

    def test_ipc_149_sale_defamatory(self, ipc_to_bns):
        assert ipc_to_bns["149"]["new"] == "163"

    def test_ipc_150_importing_defamatory(self, ipc_to_bns):
        assert ipc_to_bns["150"]["new"] == "164"

    def test_ipc_151_obscene_books(self, ipc_to_bns):
        assert ipc_to_bns["151"]["new"] == "165"

    def test_ipc_152_sale_obscene(self, ipc_to_bns):
        assert ipc_to_bns["152"]["new"] == "166"

    def test_ipc_153_obscene_acts(self, ipc_to_bns):
        assert ipc_to_bns["153"]["new"] == "167"

    def test_ipc_154_obscene_songs(self, ipc_to_bns):
        assert ipc_to_bns["154"]["new"] == "168"

    def test_ipc_155_causing_drunkenness(self, ipc_to_bns):
        assert ipc_to_bns["155"]["new"] == "169"

    def test_ipc_156_liquor_public(self, ipc_to_bns):
        assert ipc_to_bns["156"]["new"] == "170"

    def test_ipc_157_gambling_public(self, ipc_to_bns):
        assert ipc_to_bns["157"]["new"] == "171"

    def test_ipc_158_found_drunk(self, ipc_to_bns):
        assert ipc_to_bns["158"]["new"] == "172"

    def test_ipc_159_punishment_gambling(self, ipc_to_bns):
        assert ipc_to_bns["159"]["new"] == "173"

    def test_ipc_160_betting_wagering(self, ipc_to_bns):
        assert ipc_to_bns["160"]["new"] == "174"

    def test_ipc_161_occupying_public(self, ipc_to_bns):
        assert ipc_to_bns["161"]["new"] == "175"

    def test_ipc_162_animal_public(self, ipc_to_bns):
        assert ipc_to_bns["162"]["new"] == "176"

    def test_ipc_163_negligent_conduct(self, ipc_to_bns):
        assert ipc_to_bns["163"]["new"] == "177"

    def test_ipc_164_creating_nuisance(self, ipc_to_bns):
        assert ipc_to_bns["164"]["new"] == "178"

    def test_ipc_165_offensive_trades(self, ipc_to_bns):
        assert ipc_to_bns["165"]["new"] == "179"

    def test_ipc_166_annoyance_drunken(self, ipc_to_bns):
        assert ipc_to_bns["166"]["new"] == "180"

    def test_ipc_167_spitting_public(self, ipc_to_bns):
        assert ipc_to_bns["167"]["new"] == "181"

    def test_ipc_168_dispute_water(self, ipc_to_bns):
        assert ipc_to_bns["168"]["new"] == "182"

    def test_ipc_169_obstructing_public(self, ipc_to_bns):
        assert ipc_to_bns["169"]["new"] == "183"

    def test_ipc_170_neglecting_safety(self, ipc_to_bns):
        assert ipc_to_bns["170"]["new"] == "184"

    def test_ipc_171_not_providing_food(self, ipc_to_bns):
        assert ipc_to_bns["171"]["new"] == "185"

    def test_ipc_172_violent_behavior(self, ipc_to_bns):
        assert ipc_to_bns["172"]["new"] == "186"

    def test_ipc_173_vagrancy(self, ipc_to_bns):
        assert ipc_to_bns["173"]["new"] == "187"

    def test_ipc_174_prostitution(self, ipc_to_bns):
        assert ipc_to_bns["174"]["new"] == "188"

    def test_ipc_175_indecent_exposure(self, ipc_to_bns):
        assert ipc_to_bns["175"]["new"] == "189"

    def test_ipc_176_loitering(self, ipc_to_bns):
        assert ipc_to_bns["176"]["new"] == "190"

    def test_ipc_177_strolling_about(self, ipc_to_bns):
        assert ipc_to_bns["177"]["new"] == "191"

    def test_ipc_178_house_breaking_spy(self, ipc_to_bns):
        assert ipc_to_bns["178"]["new"] == "192"

    def test_ipc_179_disguised_appearance(self, ipc_to_bns):
        assert ipc_to_bns["179"]["new"] == "193"

    def test_ipc_180_public_servant_unlawful(self, ipc_to_bns):
        assert ipc_to_bns["180"]["new"] == "194"

    def test_ipc_181_wearing_uniform(self, ipc_to_bns):
        assert ipc_to_bns["181"]["new"] == "195"

    def test_ipc_182_holding_house(self, ipc_to_bns):
        assert ipc_to_bns["182"]["new"] == "196"

    def test_ipc_183_abandoning_duty(self, ipc_to_bns):
        assert ipc_to_bns["183"]["new"] == "197"

    def test_ipc_184_fraudulent_stay(self, ipc_to_bns):
        assert ipc_to_bns["184"]["new"] == "198"

    def test_ipc_185_vexatious_search(self, ipc_to_bns):
        assert ipc_to_bns["185"]["new"] == "199"

    def test_ipc_186_disclosing_secret(self, ipc_to_bns):
        assert ipc_to_bns["186"]["new"] == "200"

    def test_ipc_187_false_evidence(self, ipc_to_bns):
        assert ipc_to_bns["187"]["new"] == "201"

    def test_ipc_188_fabricating_false(self, ipc_to_bns):
        assert ipc_to_bns["188"]["new"] == "202"

    def test_ipc_189_destroying_document(self, ipc_to_bns):
        assert ipc_to_bns["189"]["new"] == "203"

    def test_ipc_190_false_verification(self, ipc_to_bns):
        assert ipc_to_bns["190"]["new"] == "204"

    def test_ipc_191_false_personation(self, ipc_to_bns):
        assert ipc_to_bns["191"]["new"] == "205"

    def test_ipc_192_cheating_definition(self, ipc_to_bns):
        assert ipc_to_bns["192"]["new"] == "206"

    def test_ipc_193_cheating_personation(self, ipc_to_bns):
        assert ipc_to_bns["193"]["new"] == "207"

    def test_ipc_194_fraudulent_deed(self, ipc_to_bns):
        assert ipc_to_bns["194"]["new"] == "208"

    def test_ipc_195_fraudulent_removal(self, ipc_to_bns):
        assert ipc_to_bns["195"]["new"] == "209"

    def test_ipc_196_false_charge(self, ipc_to_bns):
        assert ipc_to_bns["196"]["new"] == "210"

    def test_ipc_197_false_evidence_accused(self, ipc_to_bns):
        assert ipc_to_bns["197"]["new"] == "211"

    def test_ipc_198_false_information(self, ipc_to_bns):
        assert ipc_to_bns["198"]["new"] == "212"

    def test_ipc_199_harboring_offender(self, ipc_to_bns):
        assert ipc_to_bns["199"]["new"] == "213"

    def test_ipc_200_taking_gratification(self, ipc_to_bns):
        assert ipc_to_bns["200"]["new"] == "214"

    def test_ipc_201_disobeying_law(self, ipc_to_bns):
        assert ipc_to_bns["201"]["new"] == "215"

    def test_ipc_202_disclosing_secrets(self, ipc_to_bns):
        assert ipc_to_bns["202"]["new"] == "216"

    def test_ipc_203_false_return(self, ipc_to_bns):
        assert ipc_to_bns["203"]["new"] == "217"

    def test_ipc_204_false_entry(self, ipc_to_bns):
        assert ipc_to_bns["204"]["new"] == "218"

    def test_ipc_205_destroying_records(self, ipc_to_bns):
        assert ipc_to_bns["205"]["new"] == "219"

    def test_ipc_206_false_certificate(self, ipc_to_bns):
        assert ipc_to_bns["206"]["new"] == "220"

    def test_ipc_207_false_declaration(self, ipc_to_bns):
        assert ipc_to_bns["207"]["new"] == "221"

    def test_ipc_208_fraudulent_attachment(self, ipc_to_bns):
        assert ipc_to_bns["208"]["new"] == "222"

    def test_ipc_209_false_claim_court(self, ipc_to_bns):
        assert ipc_to_bns["209"]["new"] == "223"

    def test_ipc_210_false_pleading(self, ipc_to_bns):
        assert ipc_to_bns["210"]["new"] == "224"

    def test_ipc_211_fabricating_false_record(self, ipc_to_bns):
        assert ipc_to_bns["211"]["new"] == "225"

    def test_ipc_212_false_affidavit(self, ipc_to_bns):
        assert ipc_to_bns["212"]["new"] == "226"

    def test_ipc_213_falsifying_accounts(self, ipc_to_bns):
        assert ipc_to_bns["213"]["new"] == "227"

    def test_ipc_214_false_valuation(self, ipc_to_bns):
        assert ipc_to_bns["214"]["new"] == "228"

    def test_ipc_215_false_receipt(self, ipc_to_bns):
        assert ipc_to_bns["215"]["new"] == "229"

    def test_ipc_216_evasion_duty(self, ipc_to_bns):
        assert ipc_to_bns["216"]["new"] == "230"

    def test_ipc_217_fraudulent_delivery(self, ipc_to_bns):
        assert ipc_to_bns["217"]["new"] == "231"

    def test_ipc_218_fraudulent_possession(self, ipc_to_bns):
        assert ipc_to_bns["218"]["new"] == "232"

    def test_ipc_219_false_shipping_bill(self, ipc_to_bns):
        assert ipc_to_bns["219"]["new"] == "233"

    def test_ipc_220_counterfeit_coin(self, ipc_to_bns):
        assert ipc_to_bns["220"]["new"] == "234"

    def test_ipc_221_counterfeit_stamp(self, ipc_to_bns):
        assert ipc_to_bns["221"]["new"] == "235"

    def test_ipc_222_using_false_stamps(self, ipc_to_bns):
        assert ipc_to_bns["222"]["new"] == "236"

    def test_ipc_223_possessing_false_stamps(self, ipc_to_bns):
        assert ipc_to_bns["223"]["new"] == "237"

    def test_ipc_224_effacing_mark(self, ipc_to_bns):
        assert ipc_to_bns["224"]["new"] == "238"

    def test_ipc_225_making_false_mark(self, ipc_to_bns):
        assert ipc_to_bns["225"]["new"] == "239"

    def test_ipc_226_tampering_property(self, ipc_to_bns):
        assert ipc_to_bns["226"]["new"] == "240"

    def test_ipc_227_making_die(self, ipc_to_bns):
        assert ipc_to_bns["227"]["new"] == "241"

    def test_ipc_228_possessing_die(self, ipc_to_bns):
        assert ipc_to_bns["228"]["new"] == "242"

    def test_ipc_229_unlawful_access(self, ipc_to_bns):
        assert ipc_to_bns["229"]["new"] == "243"

    def test_ipc_230_climbing_over(self, ipc_to_bns):
        assert ipc_to_bns["230"]["new"] == "244"

    def test_ipc_231_enclosed_ground(self, ipc_to_bns):
        assert ipc_to_bns["231"]["new"] == "245"

    def test_ipc_232_trespassing_night(self, ipc_to_bns):
        assert ipc_to_bns["232"]["new"] == "246"

    def test_ipc_233_lurking_house(self, ipc_to_bns):
        assert ipc_to_bns["233"]["new"] == "247"

    def test_ipc_234_house_breaking_night(self, ipc_to_bns):
        assert ipc_to_bns["234"]["new"] == "248"

    def test_ipc_235_returning_house(self, ipc_to_bns):
        assert ipc_to_bns["235"]["new"] == "249"

    def test_ipc_236_possession_stolen(self, ipc_to_bns):
        assert ipc_to_bns["236"]["new"] == "250"

    def test_ipc_237_receiving_stolen(self, ipc_to_bns):
        assert ipc_to_bns["237"]["new"] == "251"

    def test_ipc_238_stolen_property(self, ipc_to_bns):
        assert ipc_to_bns["238"]["new"] == "252"

    def test_ipc_239_fraudulent_delivery(self, ipc_to_bns):
        assert ipc_to_bns["239"]["new"] == "253"

    def test_ipc_240_fraudulent_receipt(self, ipc_to_bns):
        assert ipc_to_bns["240"]["new"] == "254"

    def test_ipc_241_fraudulent_landmark(self, ipc_to_bns):
        assert ipc_to_bns["241"]["new"] == "255"

    def test_ipc_242_removing_landmark(self, ipc_to_bns):
        assert ipc_to_bns["242"]["new"] == "256"

    def test_ipc_243_setting_net(self, ipc_to_bns):
        assert ipc_to_bns["243"]["new"] == "257"

    def test_ipc_244_breaking_enclosure(self, ipc_to_bns):
        assert ipc_to_bns["244"]["new"] == "258"

    def test_ipc_245_housebreaking_day(self, ipc_to_bns):
        assert ipc_to_bns["245"]["new"] == "259"

    def test_ipc_246_publicly_exposing(self, ipc_to_bns):
        assert ipc_to_bns["246"]["new"] == "260"

    def test_ipc_247_molesting_woman(self, ipc_to_bns):
        assert ipc_to_bns["247"]["new"] == "261"

    def test_ipc_248_disturbing_privacy(self, ipc_to_bns):
        assert ipc_to_bns["248"]["new"] == "262"

    def test_ipc_249_peeping_house(self, ipc_to_bns):
        assert ipc_to_bns["249"]["new"] == "263"

    def test_ipc_250_voyeurism(self, ipc_to_bns):
        assert ipc_to_bns["250"]["new"] == "264"

    def test_ipc_251_stalking(self, ipc_to_bns):
        assert ipc_to_bns["251"]["new"] == "265"

    def test_ipc_252_criminal_force_woman(self, ipc_to_bns):
        assert ipc_to_bns["252"]["new"] == "266"

    def test_ipc_253_assault_woman(self, ipc_to_bns):
        assert ipc_to_bns["253"]["new"] == "267"

    def test_ipc_310_thug(self, ipc_to_bns):
        assert ipc_to_bns["310"]["new"] == "112"

    def test_ipc_311_belonging_gang(self, ipc_to_bns):
        assert ipc_to_bns["311"]["new"] == "113"

    def test_ipc_312_concealing_design_murder(self, ipc_to_bns):
        assert ipc_to_bns["312"]["new"] == "114"

    def test_ipc_313_wrongful_restraint(self, ipc_to_bns):
        assert ipc_to_bns["313"]["new"] == "115"

    def test_ipc_332_forcible_confinement(self, ipc_to_bns):
        assert ipc_to_bns["332"]["new"] == "134"

    def test_ipc_333_criminal_force(self, ipc_to_bns):
        assert ipc_to_bns["333"]["new"] == "135"

    def test_ipc_334_assault(self, ipc_to_bns):
        assert ipc_to_bns["334"]["new"] == "136"

    def test_ipc_335_hurt_weapon(self, ipc_to_bns):
        assert ipc_to_bns["335"]["new"] == "137"

    def test_ipc_336_grievous_hurt_weapon(self, ipc_to_bns):
        assert ipc_to_bns["336"]["new"] == "138"

    def test_ipc_337_hurt_grave_provocation(self, ipc_to_bns):
        assert ipc_to_bns["337"]["new"] == "139"

    def test_ipc_338_grievous_hurt_provocation(self, ipc_to_bns):
        assert ipc_to_bns["338"]["new"] == "140"

    def test_ipc_339_wrongful_restraint_base(self, ipc_to_bns):
        assert ipc_to_bns["339"]["new"] == "141"

    def test_ipc_340_wrongful_confinement_base(self, ipc_to_bns):
        assert ipc_to_bns["340"]["new"] == "142"

    def test_ipc_343_wrongful_restriction(self, ipc_to_bns):
        assert ipc_to_bns["343"]["new"] == "145"

    def test_ipc_344_wrongful_confinement_person(self, ipc_to_bns):
        assert ipc_to_bns["344"]["new"] == "146"

    def test_ipc_345_confinement_public_servant(self, ipc_to_bns):
        assert ipc_to_bns["345"]["new"] == "147"

    def test_ipc_346_confinement_secret(self, ipc_to_bns):
        assert ipc_to_bns["346"]["new"] == "148"

    def test_ipc_347_confinement_extortion(self, ipc_to_bns):
        assert ipc_to_bns["347"]["new"] == "149"

    def test_ipc_348_confinement_false_evidence(self, ipc_to_bns):
        assert ipc_to_bns["348"]["new"] == "150"

    def test_ipc_349_force(self, ipc_to_bns):
        assert ipc_to_bns["349"]["new"] == "151"

    def test_ipc_350_criminal_force(self, ipc_to_bns):
        assert ipc_to_bns["350"]["new"] == "152"

    def test_ipc_352_punishment_assault(self, ipc_to_bns):
        assert ipc_to_bns["352"]["new"] == "154"

    def test_ipc_355_assault_criminal_force_woman(self, ipc_to_bns):
        assert ipc_to_bns["355"]["new"] == "157"

    def test_ipc_356_robbery_base(self, ipc_to_bns):
        assert ipc_to_bns["356"]["new"] == "158"

    def test_ipc_357_attempt_rob(self, ipc_to_bns):
        assert ipc_to_bns["357"]["new"] == "159"

    def test_ipc_358_extortion_base(self, ipc_to_bns):
        assert ipc_to_bns["358"]["new"] == "160"

    def test_ipc_359_punishment_extortion(self, ipc_to_bns):
        assert ipc_to_bns["359"]["new"] == "161"

    def test_ipc_360_extortion_threat_accusation(self, ipc_to_bns):
        assert ipc_to_bns["360"]["new"] == "162"

    def test_ipc_361_extortion_threat_injury(self, ipc_to_bns):
        assert ipc_to_bns["361"]["new"] == "163"

    def test_ipc_362_robbery_dacoity(self, ipc_to_bns):
        assert ipc_to_bns["362"]["new"] == "164"

    def test_ipc_363_robbery_hurt(self, ipc_to_bns):
        assert ipc_to_bns["363"]["new"] == "165"

    def test_ipc_364_dacoity_murder_base(self, ipc_to_bns):
        assert ipc_to_bns["364"]["new"] == "166"

    def test_ipc_365_belonging_dacoit(self, ipc_to_bns):
        assert ipc_to_bns["365"]["new"] == "167"

    def test_ipc_366_joining_gang_dacoits(self, ipc_to_bns):
        assert ipc_to_bns["366"]["new"] == "168"

    def test_ipc_367_harboring_dacoit(self, ipc_to_bns):
        assert ipc_to_bns["367"]["new"] == "169"

    def test_ipc_368_stolen_property_base(self, ipc_to_bns):
        assert ipc_to_bns["368"]["new"] == "170"

    def test_ipc_369_receiving_stolen_base(self, ipc_to_bns):
        assert ipc_to_bns["369"]["new"] == "171"

    def test_ipc_370_habitual_stolen(self, ipc_to_bns):
        assert ipc_to_bns["370"]["new"] == "172"


# ── Mapping Data Quality ─────────────────────────────────────────


class TestMappingDataQuality:
    def test_no_whitespace_in_section_keys(self, ipc_to_bns):
        for sec in ipc_to_bns:
            assert sec == sec.strip(), f"Whitespace in key: '{sec}'"

    def test_no_whitespace_in_bns_keys(self, bns_to_ipc):
        for sec in bns_to_ipc:
            assert sec == sec.strip(), f"Whitespace in BNS key: '{sec}'"

    def test_no_empty_notes_field(self, ipc_to_bns):
        for sec, data in ipc_to_bns.items():
            if "note" in data:
                assert data["note"], f"IPC {sec} has empty 'note'"

    def test_all_new_values_are_strings(self, ipc_to_bns):
        for sec, data in ipc_to_bns.items():
            assert isinstance(data["new"], str), (
                f"IPC {sec} 'new' is not string: {type(data['new'])}"
            )

    def test_all_names_are_strings(self, ipc_to_bns):
        for sec, data in ipc_to_bns.items():
            assert isinstance(data["name"], str), f"IPC {sec} 'name' is not string"

    def test_all_reverse_old_values_are_strings(self, bns_to_ipc):
        for sec, data in bns_to_ipc.items():
            assert isinstance(data["old"], str), f"BNS {sec} 'old' is not string"

    def test_all_reverse_names_are_strings(self, bns_to_ipc):
        for sec, data in bns_to_ipc.items():
            assert isinstance(data["name"], str), f"BNS {sec} 'name' is not string"

    def test_no_trailing_spaces_in_names(self, ipc_to_bns):
        for sec, data in ipc_to_bns.items():
            assert data["name"] == data["name"].strip(), (
                f"IPC {sec} name has trailing space"
            )

    def test_no_leading_spaces_in_names(self, ipc_to_bns):
        for sec, data in ipc_to_bns.items():
            assert data["name"] == data["name"].strip(), (
                f"IPC {sec} name has leading space"
            )

    def test_reverse_names_no_trailing_space(self, bns_to_ipc):
        for sec, data in bns_to_ipc.items():
            name = data["name"]
            assert name == name.strip(), f"BNS {sec} name has trailing space"

    def test_effective_date_format(self, mapping_data):
        date = mapping_data["SYSTEM_NOTES"]["effective_date"]
        assert "July" in date or "2024" in date

    def test_description_present(self, mapping_data):
        desc = mapping_data["SYSTEM_NOTES"]["description"]
        assert "BNS" in desc
        assert "IPC" in desc
