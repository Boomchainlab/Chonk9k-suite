import yaml
from urllib.parse import urlparse
import pytest

COMPASS_YAML_PATH = "compass.yml"


def load_compass_config(path=COMPASS_YAML_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def assert_required_keys_present(compass_doc):
    required_keys = {"name", "id", "configVersion", "typeId"}
    missing = sorted(required_keys - compass_doc.keys())
    assert not missing, f"Missing required keys: {missing}"


def assert_links_are_valid(links):
    assert isinstance(links, list), "links must be a list"
    for index, link in enumerate(links):
        assert isinstance(link, dict), f"links[{index}] must be a mapping"
        assert "type" in link, f"links[{index}] missing 'type'"
        assert "url" in link, f"links[{index}] missing 'url'"
        parsed = urlparse(link["url"])
        assert parsed.scheme in {"http", "https"}, f"links[{index}]['url'] must have http/https scheme"
        assert parsed.netloc, f"links[{index}]['url'] must have network location"


def assert_tier_valid(fields):
    assert isinstance(fields, dict), "fields must be a mapping"
    assert "tier" in fields, "fields must specify a tier"
    tier = fields["tier"]
    assert isinstance(tier, int), "tier must be an integer"
    assert 1 <= tier <= 4, "tier must be between 1 and 4 inclusive"


class TestCompassYaml:
    """pytest-based validation suite for compass.yml (testing framework: pytest with PyYAML)."""

    @pytest.fixture(scope="class")
    def compass_doc(self):
        data = load_compass_config()
        assert isinstance(data, dict), "Compass YAML must load to a mapping"
        return data

    def test_required_keys_present(self, compass_doc):
        assert_required_keys_present(compass_doc)

    @pytest.mark.parametrize(
        "field,value_type",
        [
            ("name", str),
            ("id", str),
            ("configVersion", int),
            ("typeId", str),
            ("fields", dict),
            ("links", list),
            ("relationships", dict),
            ("labels", list),
        ],
    )
    def test_field_types(self, compass_doc, field, value_type):
        assert field in compass_doc, f"{field} must be present"
        assert isinstance(compass_doc[field], value_type), f"{field} must be of type {value_type.__name__}"

    def test_allowed_type_id(self, compass_doc):
        assert compass_doc["typeId"] == "SERVICE", "typeId must remain SERVICE for this component"

    def test_config_version_is_positive(self, compass_doc):
        assert compass_doc["configVersion"] >= 1, "configVersion must be >= 1"

    def test_fields_tier_constraints(self, compass_doc):
        fields = compass_doc.get("fields")
        assert_tier_valid(fields)

    def test_links_validation(self, compass_doc):
        links = compass_doc.get("links", [])
        assert_links_are_valid(links)

    def test_repository_link_points_to_expected_repo(self, compass_doc):
        repo_urls = [link["url"] for link in compass_doc.get("links", []) if link.get("type") == "REPOSITORY"]
        assert repo_urls, "At least one REPOSITORY link is required"
        assert "https://github.com/Boomtoknlab/agu-token" in repo_urls, "Repository link must point to the expected GitHub URL"

    def test_relationships_depends_on_is_list(self, compass_doc):
        relationships = compass_doc.get("relationships")
        assert "DEPENDS_ON" in relationships, "relationships must define DEPENDS_ON"
        depends_on = relationships["DEPENDS_ON"]
        assert isinstance(depends_on, list), "DEPENDS_ON must be a list"

    def test_description_and_custom_fields_allow_null(self, compass_doc):
        assert "description" in compass_doc, "description key must exist even if null"
        assert compass_doc["description"] is None, "description should remain null when no description provided"
        assert "customFields" in compass_doc, "customFields key must exist even if null"
        assert compass_doc["customFields"] is None, "customFields should remain null when no custom fields provided"

    def test_labels_include_source_github(self, compass_doc):
        labels = compass_doc.get("labels", [])
        assert "source:github" in labels, "labels must include source:github"

    def test_yaml_round_trip(self, compass_doc, tmp_path):
        """Ensure writing and reading preserves canonical structure."""
        temp_file = tmp_path / "round_trip.yml"
        with open(temp_file, "w", encoding="utf-8") as fh:
            yaml.safe_dump(compass_doc, fh, sort_keys=True)

        with open(temp_file, "r", encoding="utf-8") as fh:
            reloaded = yaml.safe_load(fh)

        assert reloaded == compass_doc, "Round-trip serialization should preserve content"

    def test_invalid_tier_raises(self, compass_doc):
        invalid_doc = {**compass_doc, "fields": {"tier": 5}}
        with pytest.raises(AssertionError):
            assert_tier_valid(invalid_doc["fields"])

    def test_invalid_link_scheme_raises(self, compass_doc):
        invalid_doc = {
            **compass_doc,
            "links": [{"type": "REPOSITORY", "url": "ftp://example.com"}],
        }
        with pytest.raises(AssertionError):
            assert_links_are_valid(invalid_doc["links"])

    def test_missing_required_key_raises(self, compass_doc):
        incomplete = {k: v for k, v in compass_doc.items() if k != "name"}
        with pytest.raises(AssertionError):
            assert_required_keys_present(incomplete)