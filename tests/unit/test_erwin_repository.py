"""Tests for the repository XML parser and subject-area scope."""

from pathlib import Path

import pytest

from data_model_auditor.domain.audit_scope import select_audit_scope
from data_model_auditor.domain.data_model import key_group_kind
from data_model_auditor.infrastructure.erwin.repository_xml import (
    ErwinXmlError,
    parse_erwin_repository,
)

_EXPORT = """<?xml version="1.0" encoding="UTF-8"?>
<erwin Format="erwin_Repository" FileVersion="10.0.36463">
  <Model id="model">
    <ModelProps>
      <Name>Sample</Name>
      <Long_Id>model</Long_Id>
      <Target_Server>172</Target_Server>
      <DBMS_Major_Version>15</DBMS_Major_Version>
      <DBMS_Minor_Version>0</DBMS_Minor_Version>
    </ModelProps>
    <Subject_Area_Groups>
      <Subject_Area id="sales">
        <Subject_AreaProps>
          <Name>Sales</Name>
          <Long_Id>sales</Long_Id>
          <Definition>Sales area</Definition>
          <User_Attached_Objects_Ref_Array>
            <User_Attached_Objects_Ref>customer</User_Attached_Objects_Ref>
          </User_Attached_Objects_Ref_Array>
        </Subject_AreaProps>
      </Subject_Area>
      <Subject_Area id="billing">
        <Subject_AreaProps>
          <Name>Billing</Name>
          <Long_Id>billing</Long_Id>
          <Auto_Populate_With_All_Objects>false</Auto_Populate_With_All_Objects>
          <User_Attached_Objects_Ref_Array>
            <User_Attached_Objects_Ref>order</User_Attached_Objects_Ref>
          </User_Attached_Objects_Ref_Array>
        </Subject_AreaProps>
      </Subject_Area>
      <Subject_Area id="entire">
        <Subject_AreaProps>
          <Name>Entire</Name>
          <Long_Id>entire</Long_Id>
          <Auto_Populate_With_All_Objects>true</Auto_Populate_With_All_Objects>
        </Subject_AreaProps>
      </Subject_Area>
    </Subject_Area_Groups>
    <Entity_Groups>
      <Entity id="customer">
        <EntityProps>
          <Name>Customer</Name>
          <Physical_Name>CUSTOMER</Physical_Name>
          <Long_Id>customer</Long_Id>
          <Definition>Customer entity</Definition>
        </EntityProps>
        <Attribute_Groups>
          <Attribute id="c1">
            <AttributeProps>
              <Name>Customer Id</Name>
              <Physical_Name>CUSTOMER_ID</Physical_Name>
              <Long_Id>c1</Long_Id>
              <Logical_Data_Type>CHAR</Logical_Data_Type>
              <Physical_Data_Type>CHAR(18)</Physical_Data_Type>
              <Null_Option_Type>1</Null_Option_Type>
              <Definition>Identifier</Definition>
            </AttributeProps>
            <Default_Constraint_Usage_Groups>
              <Default_Constraint_Usage id="d1">
                <Default_Constraint_UsageProps>
                  <Name>DF_CUSTOMER_ID</Name>
                  <Server_Value>('0')</Server_Value>
                </Default_Constraint_UsageProps>
              </Default_Constraint_Usage>
            </Default_Constraint_Usage_Groups>
          </Attribute>
          <Attribute id="c2">
            <AttributeProps>
              <Name>Customer Name</Name>
              <Physical_Name>CUSTOMER_NAME</Physical_Name>
              <Long_Id>c2</Long_Id>
              <Null_Option_Type>0</Null_Option_Type>
            </AttributeProps>
          </Attribute>
        </Attribute_Groups>
        <Key_Group_Groups>
          <Key_Group id="pk1">
            <Key_GroupProps>
              <Name>PK_CUSTOMER</Name>
              <Physical_Name>PK_CUSTOMER</Physical_Name>
              <Long_Id>pk1</Long_Id>
              <Key_Group_Type>PK</Key_Group_Type>
              <Is_Unique>true</Is_Unique>
            </Key_GroupProps>
            <Key_Group_Member_Groups>
              <Key_Group_Member id="m1">
                <Key_Group_MemberProps>
                  <Long_Id>m1</Long_Id>
                  <Name>Customer Id</Name>
                  <Physical_Name>CUSTOMER_ID</Physical_Name>
                  <Attribute_Ref>c1</Attribute_Ref>
                </Key_Group_MemberProps>
              </Key_Group_Member>
            </Key_Group_Member_Groups>
          </Key_Group>
        </Key_Group_Groups>
      </Entity>
      <Entity id="order">
        <EntityProps>
          <Name>Order</Name>
          <Physical_Name>ORDER</Physical_Name>
          <Long_Id>order</Long_Id>
        </EntityProps>
        <Attribute_Groups>
          <Attribute id="o1">
            <AttributeProps>
              <Name>Customer Id</Name>
              <Physical_Name>CUSTOMER_ID</Physical_Name>
              <Long_Id>o1</Long_Id>
              <Parent_Attribute_Ref>c1</Parent_Attribute_Ref>
              <Parent_Relationship_Ref>r1</Parent_Relationship_Ref>
            </AttributeProps>
          </Attribute>
        </Attribute_Groups>
      </Entity>
    </Entity_Groups>
    <Relationship_Groups>
      <Relationship id="r1">
        <RelationshipProps>
          <Name>Customer Order</Name>
          <Long_Id>r1</Long_Id>
          <Parent_Entity_Ref>customer</Parent_Entity_Ref>
          <Child_Entity_Ref>order</Child_Entity_Ref>
          <Key_Group_Ref>pk1</Key_Group_Ref>
        </RelationshipProps>
      </Relationship>
    </Relationship_Groups>
  </Model>
</erwin>
"""


def test_repository_export_keeps_names_keys_and_subject_areas(tmp_path: Path) -> None:
    path = tmp_path / "model.xml"
    path.write_text(_EXPORT, encoding="utf-8")

    model = parse_erwin_repository(path)

    assert model.name == "Sample"
    assert model.target_server == "172"
    customer = model.tables[0]
    assert customer.physical_name == "CUSTOMER"
    assert customer.columns[0].nullable is False
    assert customer.columns[1].nullable is True
    assert key_group_kind(customer.key_groups[0].key_group_type) == "primary"
    assert customer.key_groups[0].members[0].attribute_id == "c1"
    assert customer.key_groups[0].is_unique is True
    assert customer.columns[0].default_value == "('0')"
    assert customer.columns[1].default_value == ""
    migrated = model.tables[1].columns[0]
    assert migrated.parent_attribute_id == "c1"
    assert migrated.parent_relationship_id == "r1"
    assert model.relationships[0].child_entity_id == "order"
    sales = select_audit_scope(model, "Sales")
    billing = select_audit_scope(model, "Billing")
    entire = select_audit_scope(model, "Entire")
    assert [table.origin_id for table in sales.tables] == ["customer"]
    assert [table.origin_id for table in billing.tables] == ["order"]
    assert [table.origin_id for table in entire.tables] == ["customer", "order"]


def test_repository_export_rejects_a_document_type(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.xml"
    path.write_text(
        '<!DOCTYPE erwin [<!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini">]><erwin/>',
        encoding="utf-8",
    )

    with pytest.raises(ErwinXmlError):
        parse_erwin_repository(path)


def test_repository_export_rejects_another_xml_format(tmp_path: Path) -> None:
    path = tmp_path / "standard.xml"
    path.write_text('<erwin Format="erwin_Standard"><Model/></erwin>', encoding="utf-8")

    with pytest.raises(ErwinXmlError):
        parse_erwin_repository(path)
