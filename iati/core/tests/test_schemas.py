"""A module containing tests for the library representation of Schemas."""
from lxml import etree
import pytest
import iati.core.codelists
import iati.core.default
import iati.core.exceptions
import iati.core.schemas
import iati.core.tests.utilities


def default_activity_schema():
    """Create a very basic acivity schema.

    Returns:
        iati.core.ActivitySchema: An ActivitySchema that has been initialised based on the default IATI Activity Schema.

    """
    schema_name = iati.core.tests.utilities.SCHEMA_ACTIVITY_NAME_VALID

    return iati.core.default.schema(schema_name)


def default_organisation_schema():
    """Create a very basic organisaion schema.

    Returns:
        iati.core.OrganisaionSchema: An OrganisaionSchema that has been initialised based on the default IATI Organisaion Schema.

    """
    schema_name = iati.core.tests.utilities.SCHEMA_ORGANISATION_NAME_VALID

    return iati.core.default.schema(schema_name)


class TestSchemas(object):
    """A container for tests relating to Schemas."""

    @pytest.fixture(params=[
        iati.core.tests.utilities.SCHEMA_ACTIVITY_NAME_VALID,
        iati.core.tests.utilities.SCHEMA_ORGANISATION_NAME_VALID
    ])
    def schemas_initialised(self, request):
        """Create both an ActivitySchema and OrganisaionSchema class.
        For use where both ActivitySchema and OrganisaionSchema must produce the same result.

        Returns:
            iati.core.ActivitySchema / iati.core.OrganisaionSchema: An activity and organisaion that has been initialised based on the default IATI Activity and Organisaion schemas.

        """
        schema_name = request.param

        return iati.core.default.schema(schema_name)

    @pytest.mark.parametrize("schema_type, expected_value", [
        (default_activity_schema, 'iati-activities'),
        (default_organisation_schema, 'iati-organisations')
    ])
    def test_schema_default_attributes(self, schema_type, expected_value):
        """Check a Schema's default attributes are correct."""
        schema = schema_type()

        assert schema.root_element_name == expected_value

    def test_schema_define_from_xsd(self, schemas_initialised):
        """Check that a Schema can be generated from an XSD definition."""
        schema = schemas_initialised

        assert isinstance(schema.codelists, set)
        assert len(schema.codelists) == 0

    @pytest.mark.parametrize("schema_name, expected_local_element", [
        (iati.core.tests.utilities.SCHEMA_ACTIVITY_NAME_VALID, 'iati-activities'),
        (iati.core.tests.utilities.SCHEMA_ORGANISATION_NAME_VALID, 'iati-organisations')
    ])
    def test_schema_init_schema_containing_includes(self, schema_name, expected_local_element):
        """For a schema that includes another schema, check that includes are flattened correctly.

        In a full flatten of included elements as `<xi:include href="NAME.xsd" parse="xml" />`, there may be nested `schema` elements and other situations that are not permitted.

        This checks that the flattened xsd is valid and that included elements can be accessed.

        Todo:
            Assert that the flattened XML is a valid Schema.

            Test that this works with subclasses of iati.core.Schema: iati.core.ActivitySchema and iati.core.OrganisationSchema

        """
        schema = iati.core.default.schema(schema_name)

        element_name_in_flattened_schema = 'reporting-org'
        element_in_original_schema = schema.get_xsd_element(expected_local_element)
        element_in_flattened_schema = schema.get_xsd_element(element_name_in_flattened_schema)
        xsd_include_element = schema._schema_base_tree.find(
            'xsd:include', namespaces=iati.core.constants.NSMAP
        )
        xi_include_element = schema._schema_base_tree.find(
            'xi:include', namespaces={'xi': 'http://www.w3.org/2001/XInclude'}
        )
        xsd_schema_element = schema._schema_base_tree.find(
            'xsd:schema', namespaces=iati.core.constants.NSMAP
        )

        assert isinstance(element_in_flattened_schema, etree._Element)
        assert isinstance(element_in_original_schema, etree._Element)
        assert xsd_include_element is None
        assert xi_include_element is None
        assert xsd_schema_element is None

    def test_schema_init_schema_containing_no_includes(self):
        """For a schema that does not includes another schema, test that no flattening takes place.

        This test compares the etree.tostring results of the same input file which is instantiated through:
          i) iati.core.Schema, and
          ii) directly from etree.fromstring.

        """
        schema = iati.core.Schema(iati.core.tests.utilities.PATH_XSD_NON_IATI)
        xsd_bytes = iati.core.resources.load_as_bytes(iati.core.tests.utilities.PATH_XSD_NON_IATI)
        schema_direct_from_file = etree.fromstring(xsd_bytes)

        str_schema = etree.tostring(schema._schema_base_tree)
        str_schema_direct_from_file = etree.tostring(schema_direct_from_file)

        assert str_schema == str_schema_direct_from_file

    def test_schema_codelists_add(self, schemas_initialised):
        """Check that it is possible to add Codelists to the Schema."""
        codelist_name = "a test Codelist name"
        schema = schemas_initialised
        codelist = iati.core.Codelist(codelist_name)

        schema.codelists.add(codelist)

        assert len(schema.codelists) == 1

    def test_schema_codelists_add_twice(self, schemas_initialised):
        """Check that it is not possible to add the same Codelist to a Schema multiple times."""
        codelist_name = "a test Codelist name"
        schema = schemas_initialised
        codelist = iati.core.Codelist(codelist_name)

        schema.codelists.add(codelist)
        schema.codelists.add(codelist)

        assert len(schema.codelists) == 1

    def test_schema_codelists_add_duplicate(self, schemas_initialised):
        """Check that it is not possible to add multiple functionally identical Codelists to a Schema."""
        codelist_name = "a test Codelist name"
        schema = schemas_initialised
        codelist = iati.core.Codelist(codelist_name)
        codelist2 = iati.core.Codelist(codelist_name)

        schema.codelists.add(codelist)
        schema.codelists.add(codelist2)

        assert len(schema.codelists) == 1

    @pytest.mark.parametrize("schema_type, xsd_element_name, expected_type", [
        (default_activity_schema, 'iati-activities', etree._Element),
        (default_activity_schema, 'iati-activity', etree._Element),
        (default_activity_schema, 'activity-date', etree._Element),
        (default_activity_schema, 'provider-org', etree._Element),  # The 'provider-org' element is deeply nested XSD element.
        (default_activity_schema, 'element-name-that-does-not-exist', type(None)),
        (default_organisation_schema, 'iati-organisations', etree._Element),
        (default_organisation_schema, 'organisation-identifier', etree._Element),  # The 'organisation-identifier' is defined within the 'iati-organisation' element.
        (default_organisation_schema, 'sector', type(None))  # There is no 'sector' element within the organisation schema.
    ])
    def test_get_xsd_element(self, schema_type, xsd_element_name, expected_type):
        """Check that an lxml object is returned to represent an XSD element.

        Todo
            Test for elements that should be contained within a flattened schema.
        """
        schema = schema_type()

        result = schema.get_xsd_element(xsd_element_name)

        assert isinstance(result, expected_type)

    @pytest.mark.parametrize("schema_type, xsd_element_name, num_expected_child_elements", [
        (default_activity_schema, 'iati-activities', 1),
        (default_activity_schema, 'contact-info', 8),
        (default_activity_schema, 'iati-identifier', 0),  # Contains no child elements
        (default_organisation_schema, 'iati-organisations', 1),
        (default_organisation_schema, 'total-budget', 4),
        (default_organisation_schema, 'organisation-identifier', 0)  # Contains no child elements
    ])
    def test_get_child_xsd_elements(self, schema_type, xsd_element_name, num_expected_child_elements):
        """Check that a list of lxml objects are returned to represent all child XSD elements. Also check that each item in the result is of the expected type.

        Todo
            Test for elements that should be contained within a flattened schema.
        """
        schema = schema_type()
        parent_element = schema.get_xsd_element(xsd_element_name)

        result = schema.get_child_xsd_elements(parent_element)

        assert isinstance(result, list)
        assert len(result) == num_expected_child_elements
        for item in result:
            assert isinstance(item, etree._Element)

    @pytest.mark.parametrize("schema_type, xsd_element_name, num_expected_attributes", [
        (default_activity_schema, 'iati-activities', 3),
        (default_activity_schema, 'iati-activity', 6),
        (default_activity_schema, 'iati-identifier', 0),  # Contains no attributes
        (default_organisation_schema, 'iati-organisations', 2),
        (default_organisation_schema, 'iati-organisation', 3),
        (default_organisation_schema, 'organisation-identifier', 0)  # Contains no attributes
    ])
    def test_get_attributes_in_xsd_element(self, schema_type, xsd_element_name, num_expected_attributes):
        """Check that a list of lxml objects are returned to represent the attributes contained within a given XSD element. Also check that each item in the result is of the expected type.

        Todo
            Test for attributes that should be contained within elements that are part of a flattened schema.
        """
        schema = schema_type()
        element = schema.get_xsd_element(xsd_element_name)

        result = schema.get_attributes_in_xsd_element(element)

        assert isinstance(result, list)
        assert len(result) == num_expected_attributes
        for item in result:
            assert isinstance(item, etree._Element)

    @pytest.mark.parametrize("element_index, expected_name", [
        (0, 'note'),
        (1, 'to'),
        (2, 'from'),
        (3, 'heading'),
        (4, 'body')
    ])
    def test_get_xsd_element_name(self, element_index, expected_name):
        """Test that an expected name is found within a mock xsd:element.

        Todo:
            Move the mock xsd file out of the resources/test_data/202 folder, as it is not version specific.

            Rename the mock xsd file with a .xsd file extension.

            Test for a case where there is no xsd:element/@name.  In which case, test that None is returned.
        """
        schema = iati.core.Schema(iati.core.tests.utilities.PATH_XSD_NON_IATI)
        elements = schema._schema_base_tree.findall(
            '//xsd:element',
            namespaces=iati.core.constants.NSMAP
        )

        result = schema.get_xsd_element_name(elements[element_index])

        assert result == expected_name
