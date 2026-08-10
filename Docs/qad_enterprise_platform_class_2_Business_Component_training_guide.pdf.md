QAD logo

# QAD

## Class 2: QAD Enterprise Platform - Business Components

By Don Springer

QAD Enterprise Platform

# Topics

* Apps

* App Data and Configuration Data

* Design Layout

* Business Components

* Form, Browses & Views

* Deployment

* Export & Import of Data

* Reverting & Redeploy

QAD logo

<page_number>2</page_number>

# New App

QAD logo

<page_number>3</page_number>

**QAD Enterprise Platform**

# Apps

Screenshot of QAD Enterprise Platform interface showing a search for "apps" with results "Apps" and "AppServer Services". A red circle highlights the "Apps" result, with an arrow pointing to a text box.

Choose “Apps” from the menu.

4

# QAD Enterprise Platform

# New App

Screenshot of the Apps management interface in QAD Enterprise Platform, showing a list of applications with columns for App, App URI, App Label, Description, System Default, App Version, and Platform Version. A red circle highlights the "+ New" button.

Click New to create a new App.

App is a container which includes one or several business components according to their business logic

<page_number>5</page_number>

# QAD Enterprise Platform

# New App: Training

Screenshot of QAD Enterprise Platform interface showing the creation of a new app named "Training" with fields for App URI, App Label, and Description.

New app is "Training"

**Display Name**: Training
**Description**: App for Training

Then Click Save.

<page_number>6</page_number>

QAD Enterprise Platform

# App Dependencies

Screenshot of the QAD Enterprise Platform interface showing App Dependencies for a "Training" app. The screen displays fields for App URI (urn:app:com.extensions.training), App Label, and a list of dependencies including "urn:app:com.qad.qracore" marked as Implicit.

By default, all Apps depend on QRA Core.

But you can add dependencies on other Apps in case of need.

<page_number>7</page_number>

QAD Enterprise Platform

# My Developer Settings

Screenshot of the My Developer Settings interface showing the Active App configuration section.

Open "My Developer Settings" from the Menu

Change Active App dropdown selection to "Use Custom".

Then click the search icon to find newly created app.

<page_number>

8
</page_number>

**QAD Enterprise Platform**

# My Developer Settings

Screenshot of the Apps selection window in QAD Enterprise Platform showing a search for "Training" and a resulting row with App Label "Training" and Description "App for Training".

Choose Training from the Apps selection window.

<page_number>9</page_number>

# QAD Enterprise Platform

# My Developer Settings

Screenshot of My Developer Settings interface showing Active App configuration

Verify that the Active App was set as Training and then click Save.

**Save**

Cancel

<page_number>10</page_number>

# App Data and Configuration Data

QAD logo

<page_number>11</page_number>

QAD logo

# QAD Enterprise Platform

# What is Configuration Data?

Configuration Data is a way to save system data. It allows environment configurations to be quickly and easily transferred without the need to involve QAD Cloud support

## App Data

Adaptive solutions

Need to go through SDLC

Mandatory part of app

VS.

## Configuration Data

Used to configure or personalize Adaptive according to user needs

Does not need to go through SDLC

Additional configuration of app

| Used to create and extend | Used to configure or personalize |
| ------------------------- | -------------------------------- |
| Adaptive solutions        | Adaptive according to user needs |
| Need to go through SDLC   | Does not need to go through SDLC |
| Mandatory part of app     | Additional configuration of app  |


<page_number>12</page_number>

QAD Enterprise Platform

# Which Artifacts can be saved as Configuration Data?

**Artifact** is the specific physical piece of information that is used or produced by a software development process, or by deployment or using of a system.

* Business Components

* Lookup Definitions

* Formula Fields

* Approvals

* Event Handlers

* Default Roles

* Field Security

arrow down icon

App Data Only

* Design Layout

* Stored View

* Theme, Theme Workspace

* Notification Template

* Notification Template Message

arrow down icon

In an App\*

\*In Dev Environments

arrow down icon

In Configuration Data

* Activity Tracking, Alert

* Field Property Overrides

* Role, Menu, & Permissions

* Action Center

* KPI

arrow down icon

Configuration Data Only

<page_number>

13
</page_number>

QAD Enterprise Platform

# Saving Configuration Data: Dev Environment

Screenshot of My Developer Settings in QAD Enterprise Platform showing the "Save New Artifacts to Configuration Data as Default" checkbox selected.

Set default option in My Developer Settings

* It does not prevent user from selecting Current App from dropdown

## Development Environment

* Save artifacts to App Data or Configuration Data

Diagram showing the "Saved To" dropdown menu with options "App Data" and "Configuration Data".

## Production or Test Environment:

* All new artifacts are saved in Configuration Data.

Screenshot showing "Save To" field set to "Configuration Data".

<page_number>

14
</page_number>

<mark>QAD Enterprise Platform</mark>

# Transferring Configuration Data

Screenshot of the Configuration Data screen in QAD Enterprise Platform showing a list of artifacts such as Action Center, Active Stored View, KPI, and Role, Menu & Permissions.

15

# Design Layout

QAD logo

<page_number>18</page_number>

QAD Enterprise Platform

# Design Layout

Screenshot of the QAD Countries screen showing the "More" dropdown menu with the "Design Layout" option highlighted by a red arrow.

Design Layout is a tool which provides possibility to configure already existing views.

As an example, let’s change a Countries form.

Open Countries screen.

In More drop-down click on Design Layout option.

<page_number>17</page_number>

QAD Enterprise Platform

# Design Layout

| Select a Design Layout + New Layout Manage Active Layouts<br/>Name | Select a Design Layout + New Layout Manage Active Layouts<br/>Description | Select a Design Layout + New Layout Manage Active Layouts<br/>Active | Select a Design Layout + New Layout Manage Active Layouts<br/>Saved To |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| System Wide                                                        |                                                                           |                                                                      |                                                                        |
| Default                                                            | Default                                                                   | Yes                                                                  | App Data                                                               |


Create a new Design Layout.

<page_number>18</page_number>

QAD Enterprise Platform

# Design Layout

Name the new layout as ‘Training’.

Select ‘Saved To’ value as ‘App Data’

Click Continue button.

Screenshot of the "New Layout" dialog box in QAD Enterprise Platform, showing fields for Name (Training), Description, Layout Context (System Wide), Saved To (App Data), App (Training), and App URI, along with a template selection table and Continue/Cancel buttons.

<page_number>19</page_number>

# QAD Enterprise Platform

# Design Layout

Screenshot of the QAD Enterprise Platform Design Layout interface showing the Form Builder for the Countries form. The interface displays various sections like Main, Compliance, and Tax with their respective fields and layout options. Red arrows point from the descriptive text on the right to specific elements in the form builder: the Comment Index field, the Compliance section, and the Tax section.

The Form Builder is opened.

Here you can see the structure of Country form, including fields and panels which could be hidden by the default logic (such as: Comment Index field or Compliance and Tax panels).

20

# QAD Enterprise Platform

# Design Layout

Screenshot of the QAD Design Layout interface showing the Countries maintenance screen with the Compliance panel selected and its properties displayed in the right sidebar.

Click on the Compliance panel.

In the top right, you will see properties of the selected element.

<page_number>21</page_number>

QAD Enterprise Platform

# Design Layout

Screenshot of the Countries Design Layout screen in QAD Enterprise Platform, showing the form designer with fields like Country, Description, and panels for Main, Compliance, Tax, and Notes. Red arrows point from the Comment Index field, Compliance panel, and Tax panel to a text box on the right.

You can also remove selected elements (field or panel) from the screen.

Select and remove Comment Index field, Compliance, Tax and Notes panels.

We don’t need those elements in our further examples.

<page_number>22</page_number>

**QAD Enterprise Platform**

# Design Layout

Screenshot of the QAD Enterprise Platform Design Layout interface showing form builder properties and field configuration.

Save updated layout

Close Form Builder.

23

23

**QAD Enterprise Platform**

# Design Layout

Screenshot of QAD Enterprise Platform showing the Countries browse screen with the "More" dropdown menu open and "Design Layout" selected.

Now we should set newly created layout as active.

Click on Design Layout option In More drop-down again.

<page_number>24</page_number>

QAD Enterprise Platform

# Design Layout

Screenshot of the Select a Design Layout window showing a table with columns Name, Description, Active, and Saved To. A red arrow points from a text box to the Manage Active Layouts button.

| Select a Design Layout + New Layout Manage Active Layouts x<br/>Name | Select a Design Layout + New Layout Manage Active Layouts x<br/>Description | Select a Design Layout + New Layout Manage Active Layouts x<br/>Active | Select a Design Layout + New Layout Manage Active Layouts x<br/>Saved To |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| System Wide                                                          |                                                                             |                                                                        |                                                                          |
| Default                                                              | Default                                                                     | Yes                                                                    | App Data                                                                 |
| Training                                                             |                                                                             | No                                                                     | App Data                                                                 |


Click Manage Active Layouts button.

<page_number>25</page_number>

**QAD Enterprise Platform**

# Design Layout

**Manage Active Layouts** [x]

| Active        | Name     | Description | Saved To | Last Modified     | Last Modified By |
| ------------- | -------- | ----------- | -------- | ----------------- | ---------------- |
| v System Wide |          |             |          |                   |                  |
| \[no]         | Default  | Default     | App Data | 1/1/1970 3:00 AM  |                  |
| \[yes]        | Training |             | App Data | 4/23/2025 6:29 PM | mfg              |


Apply Cancel

Select Training and click Apply.

<page_number>

26
</page_number>

QAD Enterprise Platform

# Design Layout

Screenshot of the "Select a Design Layout" modal window in QAD Enterprise Platform, showing a table with layout options like "Default" and "Training".

Close modal window and reload the page

<page_number>

27
</page_number>

QAD Enterprise Platform

# Design Layout

Screenshot of the QAD Enterprise Platform interface showing a "Countries" list and a detailed "Design Layout" form for country #BE (BELGIUM). The form includes fields for Country, Description, Active checkbox, European Union Member checkbox, Address Format, Alternate Country, Intrastat Currency, and Fiscal Country.

Open the form.

You can see that it’s possible to leave only that fields, which are make sense for required business logic.

<page_number>28</page_number>

# Field Overrides

QAD logo

<page_number>18</page_number>

QAD Enterprise Platform

# Field Overrides

Screenshot of the Overrides configuration screen in QAD Enterprise Platform

Field Overrides is a mechanism which allow you to modify already existing field.

You can make field mandatory, define default value, change label or field format.

Field Overrides are accessible in the Design Layout or from Business Component > Fields > Details > Overrides.

QAD logo

<page_number>

30
</page_number>

QAD Enterprise Platform

# Field Overrides

Screenshot of QAD Enterprise Platform showing the Countries browse screen with the "More" menu open and "Design Layout" selected.

Let’s use Design Layout to change Address Format field label.

In More drop-down click on Design Layout option.

<page_number>31</page_number>

QAD Enterprise Platform

# Field Overrides

Screenshot of the "Select a Design Layout" dialog box in QAD Enterprise Platform, showing a table with layout options. The "Training" layout is selected (highlighted in dark blue), with "Active" set to "Yes" and "Saved To" as "App Data". A red arrow points from a text box at the bottom right to the selected "Training" row.

Select Training layout and click Continue

<page_number>32</page_number>

QAD Enterprise Platform

# Field Overrides

Screenshot of the Countries Design Layout interface in QAD Enterprise Platform, showing the Address Format field selected and its properties panel on the right, including the Manage Overrides button.

Select Address Format field and on the right-side scroll field properties till button Manage Overrides.

Click on it.

<page_number>33</page_number>

# QAD Enterprise Platform

# Field Overrides

Screenshot of Business Component Field Properties modal window showing the Overrides panel with Field Label Override checked and set to Zip Code Position.

In opened modal window find Overrides panel.

Check the Field Label Override option and put Zip Code Position value into the enabled field.

<page_number>34</page_number>

QAD Enterprise Platform

# Field Overrides

Screenshot of Business Component Field Properties dialog showing Overrides tab with System Property Overrides for postalFormat field.

Click Save, close Form Builder and reload the page.

35

QAD Enterprise Platform

# Field Overrides

Screenshot of the Countries screen in QAD Enterprise Platform showing a record for Belgium with the field label "Zip Code Position" highlighted.

Click New

Pay attention that label was successfully changed to Zip Code Position

<page_number>

36
</page_number>

# QAD Enterprise Platform

# Field Overrides

Screenshot of the Business Components Countries > Fields interface showing field details and overrides for CountryID.

You can manage field overrides directly in Business Component.

To do this find Fields panel and click Details link.

Then scroll to Overrides panel.

<page_number>37</page_number>

# Translations

QAD logo

<page_number>25</page_number>

**QAD Enterprise Platform**

# Translations

| String Code             | Text                            | Context | Max Character Length | Overrides | Saved To | App | App URI |
| ----------------------- | ------------------------------- | ------- | -------------------- | --------- | -------- | --- | ------- |
| -                       | -                               | -       | 255                  | No        | App Data |     |         |
| -99                     | -99                             |         |                      | No        | App Data |     |         |
| YES YES                 | YES 255 No App Data EMPTY EMPTY |         |                      |           |          |     |         |
| (N)\_DAYS\_AGO          | (n) Days Ago                    |         |                      | Yes       | App Data |     |         |
| (N)\_DAYS\_AHEAD        | (n) Days Ahe...                 |         |                      | No        | App Data |     |         |
| (N)\_FISCAL\_PERIOD...  | (n) GL Perio...                 |         |                      | No        | App Data |     |         |
| (N)\_FISCAL\_PERIOD...  | (n) GL Perio...                 |         |                      | No        | App Data |     |         |
| (N)\_FISCAL\_YEARS\_... | (n) GL Years ...                |         |                      | No        | App Data |     |         |


Open the Translations screen

Here you can see all translation which are currently available in the system. To create your own, click New.

<page_number>39</page_number>

**QAD Enterprise Platform**

# Translations

Screenshot of the Translations interface in QAD Enterprise Platform, showing a list of string codes and a detail view for creating a new translation record.

In the main panel you should define String Code (a unique identifier of the translation)

Put ZIP_CODE_POSITION, fill Context field and Save the record.

<page_number>40</page_number>

QAD Enterprise Platform

# Translations

Screenshot of the Translations interface in QAD Enterprise Platform showing the configuration for CNFG:ZIP_CODE_POSITION, including a list of string codes and a detail view with a Translations sub-grid where "Zip Code Position" is being edited for the English locale.

Add translations for each required language.

<page_number>41</page_number>

**QAD Enterprise Platform**

# Translations

Screenshot of Business Component Field Properties window showing field overrides for postalFormat (Address Format).

Open Field Overrides for the Address Format screen one more time.

Click on lookup icon.

<page_number>42</page_number>

QAD Enterprise Platform

# Translations

| String Code           | Text                  | Context                  | Max Character Length | Overrides | Saved To          |
| --------------------- | --------------------- | ------------------------ | -------------------- | --------- | ----------------- |
| CNFG:ZIP\_CODE\_PO... | Zip Code Position     | Tranlsation for the Z... | 255                  | No        | Configuration Dat |
| mfg-END\_USERS\_BY... | End Users By Zip Code |                          | 000                  | No        | App Data          |
| mfg-ZIP\_CODE         | Zip Code              |                          |                      | No        | App Data          |
| mfg-ZIP\_CODE-short   | Zip                   |                          |                      | No        | App Data          |
| mfg-ZIP\_CODES        | Zip Codes             |                          | 000                  | No        | App Data          |


In the opened browse add "String Code contains ZIP_CODE" filter and you will be able to find just created translation.

Select it.

<page_number>43</page_number>

QAD Enterprise Platform

# Translations

Screenshot of Business Component Field Properties dialog in QAD Enterprise Platform

Click Save, close Form Builder and reload the page.

### Business Component Field Properties

**Design Layout > Business Component Field Properties**

**Changes to these properties affect all layouts for this business component**

* **Field**: postalFormat
* **Field Label**: Address Format

#### Overrides

* **System Property Overrides**
  * **Field Label Override**: [x] [CNFG:ZIP_CODE_POSITION]
  * **Required Override**: [ ]
  * **Default Value Override**: [ ]
  * **Length Override**: [ ]
  * **Format Override**: [ ]
  * **Saved To**: Configuration Data
  * **Remarks**:
  * **Last Modified By**: mfg (MFG Super User)
  * **Last Modified Date**: 5/12/2026

[Save] [Close]

<page_number>44</page_number>

QAD Enterprise Platform

# Field Overrides

Screenshot of the Countries maintenance screen in QAD Enterprise Platform showing field overrides for Belgium.

Click New

Pay attention that translation was successfully applied as a label text.

<page_number>

45
</page_number>

# Own Business Component

QAD logo

<page_number>25</page_number>

QAD Enterprise Platform

# New Business Component

Screenshot of QAD Enterprise Platform showing My Developer Settings and the Menu Search with Business Components highlighted.

Choose “Business Components” from the Menu.

<page_number>

47
</page_number>

QAD Enterprise Platform

# New Business Component

Click New to create Business Component.

Screenshot of the Business Components screen in QAD Enterprise Platform, highlighting the "+ New" button.

| Business Component     | Label                          | Business Component URI                                                                  | Type     | Status   | Business Document |
| ---------------------- | ------------------------------ | --------------------------------------------------------------------------------------- | -------- | -------- | ----------------- |
| AccessControlEntries   | Access Control Entry           | urn:service:com.qad.qra.security.IAccessControlEntry-AccessControlEntries               | Action   | Released | No                |
| AccessControlEntries   | SOD Validator                  | urn:service:com.qad.qra.sod.ISODValidator-AccessControlEntries                          | Action   | Released | No                |
| AccessControlEntryApps | Access Control Entry By App    | urn:be:com.qad.qra.security.IAccessControlEntryApp                                      | Standard | Released | No                |
| AccountDefaults        | Account Default                | urn:be:com.qad.base.coa.IAccountDefault                                                 | Standard | Released | No                |
| AccountGroups          | Account Groups                 | urn:be:com.qad.assetmgmt.finance.accountgroup.IAccountGroup                             | Standard | Released | No                |
| AccountInfos           | Journal Entry                  | urn:service:com.qad.financials.generalledger.journalentry.IJournalEntry-AccountInfos    | Action   | Released | No                |
| AccountInfos           | Transient Journal Entries      | urn:service:com.qad.financials.generalledger.journalentry.ITransientJournalEntry-Acc... | Action   | Released | No                |
| Accounts               | Supplier Invoice               | urn:service:com.qad.financials.purchaseledger.supplierinvoice.ISupplierInvoice-Acco...  | Action   | Released | No                |
| AccountTableFields     | Operational Account Tables ... | urn:be:com.qad.financials.systemadministration.accounttablefield.IAccountTableField     | Standard | Released | Yes               |
| AccrualConfs           | Accrual                        | urn:service:com.qad.tam.accrual.IAccrualV2-AccrualConfs                                 | Action   | Released | No                |
| AccrualV2s             | Accrual                        | urn:be:com.qad.tam.accrual.IAccrualV2                                                   | Standard | Released | No                |
| AcMemberMaints         | Maintain Membership            | urn:service:com.qad.sales.pricing.IAcMemberMaint-AcMemberMaints                         | Action   | Released | No                |


<page_number>48</page_number>

QAD Enterprise Platform

# Component Name, Label, Table, Description & Scope

Screenshot of QAD Enterprise Platform interface showing the Main tab of a Business Component configuration.

Set ‘Training’ value to:

* Business Component
* Label
* Physical Table
* Description

Set Scope to System.

QAD logo

<page_number>49</page_number>

QAD Enterprise Platform

# Field Definitions Import

Screenshot of the QAD Enterprise Platform interface showing the Field Definitions Import screen. The screen displays a list of entities on the left (e.g., AccessControlEntries, AccountDefaults, Accounts) and details for the selected entity on the right. The details include sections for Description, App URI, Options (with checkboxes for Embedded, Business Document, and Not Extensible), and a Fields section with an Import button. A table below the Fields section has columns for Primary Key, Field, Field Label, Physical Field, Formula, Lookup, Data Type, and Length. A Recalculate Formulas section is also visible at the bottom.

Select Import to Import Field Definitions from Excel

<page_number>

50
</page_number>

QAD Enterprise Platform

# Field Definitions Import

Screenshot of the Import dialog box in the QAD Enterprise Platform interface, showing fields for Data Source Type (set to File) and Source File (with a Choose file button). A red arrow points from the text instructions to the Choose file button.

Download from the materials for this class the spreadsheet BusinessComponentTraining.xlsx

Click **Choose file** and use the downloaded file.

Click **Import**.

<page_number>

51
</page_number>

QAD Enterprise Platform

# Spreadsheet for “Training” Business Component

Screenshot of Excel spreadsheet titled BusinessComponentTraining.xlsx showing training class data

Column Headings - Field Names
Subsequent Rows - Data Records (2 Classes)

<page_number>

52
</page_number>

QAD Enterprise Platform

# Primary Key, Length & Format

Fields configuration table screenshot

1. Set Primary Key: ClassName is 1; Location is 2.

2. Set Character Fields to Length 32.

The format will be set as x(32) automatically.

3. Set DurationDays and Capacity fields format to ‘>9’.

QAD logo

<page_number>53</page_number>

QAD Enterprise Platform

# Drop-Down Lists

**Drop-Down Lists**

Screenshot of the QAD Enterprise Platform interface showing the creation of a new Drop-Down List named "Area of Study" with child values: Distribution, Financial, Inventory, Manufacturing, and Purchasing. A text box to the right provides instructions: "Scroll down to Drop-Down Lists and Create New. List “Area of Study” with children: Purchasing, Inventory, Financial, Manufacturing, and Distribution. Click Save"

<page_number>

54
</page_number>

**QAD Enterprise Platform**

# Drop-Down Lists

Screenshot of the QAD Enterprise Platform interface showing the Fields tab of a Business Component named Training. The AreaOfStudy field is highlighted with a red circle around its Data Type, which is set to Drop Down (Character).

Now go back to the Field line for Area of Study and change “Area of Study” to Data Type “Drop Down”.

### Fields

Screenshot detail of the Fields table showing the configuration for a Drop Down data type. A red box highlights the row for Area of Study, and a red circle points to the selection of "Area of Study" from the Drop-Down List column.

Choose “Area of Study” from the available Drop-Down Lists.

<page_number>55</page_number>

QAD logo

**QAD Enterprise Platform**

# More about Drop-Down Lists

You can use Generalized Codes (code_mstr) for Drop-Down Lists

* Add into Generalized Codes a field that you want to make as a Drop-down list

* The field must have Character data type and should not be defined as a lookup.

* The Physical Field Name must match the name of the Generalized Code field. System will convert that field into lookup automatically

* You can also just use the name of an existing Generalized Code such as 'stat' as the physical field name.

<page_number>56</page_number>

QAD Enterprise Platform

# Field Groups

## Field Groups

Screenshot of the Field Groups interface showing a table with columns "Field Group Code" and "Field Group Label", and buttons for "+ New", "Delete", "More", and "Assign Fields".

There is no need to assign field groups for this example. We can allow all users access to all fields. However, it is possible to create field groups, and then associate them with Roles, so that users with specific roles have update rights to specific field groups.

1 Create Field Group.
2 Assign Fields.

<page_number>57</page_number>

QAD Enterprise Platform

# New Business Component

Screenshot of the QAD Enterprise Platform interface showing the New Business Component screen with tabs for Main, Fields, Relationships, Business Services, Form, Browses, Views, Java Extensions, and Deployment. The Deployment section is expanded, showing fields for Data Store URI and Import Data. The Save button is highlighted with a red circle.

Save the Business Component.

<page_number>58</page_number>

QAD Enterprise Platform

# New Business Component

### Deployment

**Data Store URI**: urn:datastore:com.extensions.extension
**Import Data**: [ ]
[Deploy]

Do not Deploy it yet.

if you do that you will get the validation error.

Next step is to create Form and View.

| Field | Error                                 |
| ----- | ------------------------------------- |
|       | There should exist at least one View. |
|       | There should exist at least one Form. |


QAD logo

<page_number>59</page_number>

QAD Enterprise Platform

# Setting Up a Form & View

## Form

Screenshot of the QAD Enterprise Platform interface showing the Form section with a "Build Form" button highlighted by a red circle and an arrow pointing from a text box that says "Scroll down to Form panel and click Build Form button." Below this is an "Event Handlers" section with a table containing columns for Timing, Active, Applies To, App, and App URI.

Scroll down to Form panel and click Build Form button.

### Event Handlers

| Timing | Active | Applies To | App | App URI |
| ------ | ------ | ---------- | --- | ------- |
|        |        |            |     |         |


<page_number>

60
</page_number>

QAD Enterprise Platform

# Form Builder

Screenshot of the QAD Form Builder interface showing layout properties for a panel.

You will find that a Panel was already added, and you can change the label to “Training”.

<page_number>

61
</page_number>

# QAD Enterprise Platform

## Form Builder

Screenshot of the Form Builder interface showing the Training Build Form layout with fields like Class Name, Location, Topic Type, and Area of Study. A sidebar on the right shows "Set Layout Properties" and "Add to Layout" sections.

1. Expand Fields > Default as shown on lower right.

2. Proceed to drag fields into the Training Panel.

3. You can also add fields to the Summary Panel.

4. Save changes and Close Form Builder.

<page_number>62</page_number>

**QAD Enterprise Platform**

# Browse

**Browses**

Screenshot of the Browses panel in QAD Enterprise Platform showing a table with columns Name, Browse URI, App, and App URI, and a toolbar with a New button circled in red.

Scroll down to Browse panel and click New.

If you don’t have any browses, you will be able to create only ‘Form Only’ views.

<page_number>63</page_number>

**QAD Enterprise Platform**

# Browse

1. Set Browse Label as “Training”.

2. In Fields panel select the Fields you want displayed in the Browse. (You can use the default selection).

3. Click Save and Close when done.

Screenshot of the QAD Enterprise Platform Browse configuration screen showing the Main and Fields sections. The Browse Label is set to "Training". The Fields table shows selected fields like ClassName, Location, TopicType, AreaOfStudy, StartDate, ClassValue, and DurationDays.

QAD logo

64

QAD Enterprise Platform

# View

Screenshot of the Views panel in the QAD Enterprise Platform interface, showing a table with columns for View Label, Description, Type, Eligible for Menu, App, and App URI. The "+ New" button is circled in red.

Source File Generation

Scroll down to Views panel and click the New.

<page_number>

65
</page_number>

# QAD Enterprise Platform

# View

1. Set View Label as “Training”.

2. Ensure that check boxes are checked as shown (which is the default).

3. In Browse panel choose earlier created Training browse.

4. Click Save and Close when done.

Screenshot of the QAD Enterprise Platform View configuration screen showing sections for Main, Options, Browse, and TS Handlers. The View Label is set to "Training", Type is "Hybrid Browse", and various checkboxes like Default, Eligible for Menu, Allow New, Allow Edit, and Allow Delete are checked.

QAD logo

QAD icon

<page_number>66</page_number>

QAD Enterprise Platform

# Deployment

Screenshot of the Deployment screen in QAD Enterprise Platform, highlighting the Data Store URI field with a red oval.

Next you are ready to Deploy. Choose where to Deploy to using: Data Store URI field search icon.

<page_number>

67
</page_number>

# QAD Enterprise Platform

## Data Store

Screenshot of the Data Stores interface in QAD Enterprise Platform, showing a table with one entry named "extension" in "Development" mode.

Select “Extension”.

Note that a Data Store must be in Development Mode in order to save a new Business Component.

<page_number>68</page_number>

**QAD Enterprise Platform**

# Deploy...

**Deployment**

Screenshot of the Deployment screen in QAD Enterprise Platform showing the Data Store URI field, Import Data checkbox, and a highlighted Deploy button. An instruction box on the right says "Click Deploy."

<page_number>69</page_number>

# QAD Enterprise Platform

# Let’s Run it

### Views

Screenshot of the Views panel in QAD Enterprise Platform showing a table with a "Training" view entry and the "Preview" button highlighted.

In the Views panel you can use the Preview button to open “Training” view.

Or you can open the Search Menu, type the name of the View you created (in this case “Training”).

<page_number>70</page_number>

# QAD Enterprise Platform

# Let’s Run it

Screenshot of QAD Enterprise Platform interface showing the Training module with a new record entry form.

Time to add a record!

<page_number>71</page_number>

# QAD Enterprise Platform

# Let’s Run it

**Training**

**Class Name**: Laser Cutter Maintenance
**Topic Type**: Maintenance
**Location**: Chicago
**Area of Study**: Manufacturing
**Start Date**: 10/6/2023 2:01 PM
**Class Value**: 80
**Duration Days**: 4
**Capacity**: 8

Enter data which is meaningful for you.

Click Save.

QAD logo

<page_number>72</page_number>

# Export / Import

QAD logo

<page_number>73</page_number>

QAD Enterprise Platform

# Export / Import

Screenshot of QAD Enterprise Platform showing the Training screen with the "More" dropdown menu open, highlighting Export and Import options.

Open More dropdown.
Here you will be able to find Import and Export options

QAD logo

<page_number>

74
</page_number>

QAD Enterprise Platform

# Export / Import

Screenshot of QAD Enterprise Platform showing the Training screen with a dropdown menu open under 'More' highlighting the 'Export' option. The table displays training classes with columns for Class Name, Location, Topic Type, Permissions, Start Date, Class Value, Duration Days, and Capacity.

Click Export to generate a template.

<page_number>

52
</page_number>

**QAD Enterprise Platform**

# Export

Screenshot of the Export interface in QAD Enterprise Platform showing Search Criteria, File Properties, and Fields selection. Red arrows point from the instructional text to the corresponding fields in the UI.

* Export as Excel

* Enter a File Name

* Choose “Export with Import Format”.

* Click the Export Button.

<page_number>76</page_number>

# QAD Enterprise Platform

# Export

Screenshot of the QAD Enterprise Platform interface showing an export notification in the Inbox.

The export file will be sent to your inbox.

Click the link which is the title of your file, to download it.

QAD logo

<page_number>77</page_number>

# QAD Enterprise Platform

# Export

| 1<br/>2<br/>3<br/>4<br/>ensions.training.Training.ITraining:Traning.Trainiperation:rovs.training.Training.ITraining.Training.ITraining.Training.Taining.Training.ITrining.Training.ning.Trainin | Import Training Training Keys<br/>Class Name<br/>ensions.training.Training.ITraining:Traning.Trainiperation:rovs.training.Training.ITraining.Training.ITraining.Training.Taining.Training.ITrining.Training.ning.Trainin | Import Training Training Keys<br/>Location<br/>ensions.training.Training.ITraining:Traning.Trainiperation:rovs.training.Training.ITraining.Training.ITraining.Training.Taining.Training.ITrining.Training.ning.Trainin | Training Training<br/>Row Data<br/>ensions.training.Training.ITraining:Traning.Trainiperation:rovs.training.Training.ITraining.Training.ITraining.Training.Taining.Training.ITrining.Training.ning.Trainin | Training Training<br/>Start Date<br/>ensions.training.Training.ITraining:Traning.Trainiperation:rovs.training.Training.ITraining.Training.ITraining.Training.Taining.Training.ITrining.Training.ning.Trainin | Training Training<br/>Duration Days<br/>ensions.training.Training.ITraining:Traning.Trainiperation:rovs.training.Training.ITraining.Training.ITraining.Training.Taining.Training.ITrining.Training.ning.Trainin | Training Training<br/>Topic Type<br/>ensions.training.Training.ITraining:Traning.Trainiperation:rovs.training.Training.ITraining.Training.ITraining.Training.Taining.Training.ITrining.Training.ning.Trainin | Training Training<br/>Area of Study<br/>ensions.training.Training.ITraining:Traning.Trainiperation:rovs.training.Training.ITraining.Training.ITraining.Training.Taining.Training.ITrining.Training.ning.Trainin | Training Training<br/>Class Value<br/>ensions.training.Training.ITraining:Traning.Trainiperation:rovs.training.Training.ITraining.Training.ITraining.Training.Taining.Training.ITrining.Training.ning.Trainin | Training Training<br/>Capacity<br/>ensions.training.Training.ITraining:Traning.Trainiperation:rovs.training.Training.ITraining.Training.ITraining.Training.Taining.Training.ITrining.Training.ning.Trainin |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 6                                                                                                                                                                                               | Laser Cutter Maintenance                                                                                                                                                                                                 | Chicago                                                                                                                                                                                                                | Training                                                                                                                                                                                                   | 10/6/2023 2:01 PM                                                                                                                                                                                            | 4                                                                                                                                                                                                               | Maintenance                                                                                                                                                                                                  | Manufacturing                                                                                                                                                                                                   | 80                                                                                                                                                                                                            | 8                                                                                                                                                                                                          |
| 7                                                                                                                                                                                               | Stamping Machine Maintenance                                                                                                                                                                                             | Detroit                                                                                                                                                                                                                | Training                                                                                                                                                                                                   | 10/7/2023 2:42 PM                                                                                                                                                                                            | 3                                                                                                                                                                                                               | Maintenance                                                                                                                                                                                                  | Manufacturing                                                                                                                                                                                                   | 80                                                                                                                                                                                                            | 3                                                                                                                                                                                                          |
| 8                                                                                                                                                                                               |                                                                                                                                                                                                                          |                                                                                                                                                                                                                        |                                                                                                                                                                                                            |                                                                                                                                                                                                              |                                                                                                                                                                                                                 |                                                                                                                                                                                                              |                                                                                                                                                                                                                 |                                                                                                                                                                                                               |                                                                                                                                                                                                            |
| 9                                                                                                                                                                                               |                                                                                                                                                                                                                          |                                                                                                                                                                                                                        |                                                                                                                                                                                                            |                                                                                                                                                                                                              |                                                                                                                                                                                                                 |                                                                                                                                                                                                              |                                                                                                                                                                                                                 |                                                                                                                                                                                                               |                                                                                                                                                                                                            |
| 10                                                                                                                                                                                              |                                                                                                                                                                                                                          |                                                                                                                                                                                                                        |                                                                                                                                                                                                            |                                                                                                                                                                                                              |                                                                                                                                                                                                                 |                                                                                                                                                                                                              |                                                                                                                                                                                                                 |                                                                                                                                                                                                               |                                                                                                                                                                                                            |
| 11                                                                                                                                                                                              |                                                                                                                                                                                                                          |                                                                                                                                                                                                                        |                                                                                                                                                                                                            |                                                                                                                                                                                                              |                                                                                                                                                                                                                 |                                                                                                                                                                                                              |                                                                                                                                                                                                                 |                                                                                                                                                                                                               |                                                                                                                                                                                                            |


Update the spreadsheet (which you just downloaded) with a new or modified records and import it back into your Business Component.

QAD logo

<page_number>78</page_number>

# QAD Enterprise Platform

# Import

Screenshot of the Import screen in QAD Enterprise Platform showing file selection, data preview table, and import button.

Click the "Choose File" button and select your file.

Note that you get a preview of the data that will be imported.

Click the import button.

<page_number>79</page_number>

# QAD Enterprise Platform

# Import

Screenshot of QAD Enterprise Platform Training page showing imported records

Now refresh Training page, and you will see the records you just imported.

QAD logo

<page_number>80</page_number>

# Deploy / Undeploy

QAD logo

<page_number>58</page_number>

QAD Enterprise Platform

# Deployed a Business Component

| Physical Field | Formula | Lookup | Data Type | Length | Format            |
| -------------- | ------- | ------ | --------- | ------ | ----------------- |
| Capacity       | \[no]   | \[no]  | Integer   |        | >9                |
| ClassName      | \[no]   | \[no]  | Character | 32     | x(32)             |
| ClassValue     | \[no]   | \[no]  | Integer   |        | ->,>>>,>>9        |
| DurationDays   | \[no]   | \[no]  | Integer   |        | >9                |
| Location       | \[no]   | \[no]  | Character | 32     | x(32)             |
| StartDate      | \[no]   | \[no]  | Datetime  |        | 99/99/9999 HH:... |
| TopicType      | \[no]   | \[no]  | Character | 32     | x(32)             |


Once Business Component is deployed, you are still able to add fields, but you cannot change a field name, type, length or format

<page_number>82</page_number>

QAD Enterprise Platform

# Undeploy / Redeploy a Business Component

| Physical Field | Formula | Lookup | Data Type | Length | Format            |
| -------------- | ------- | ------ | --------- | ------ | ----------------- |
| Capacity       | \[no]   | \[no]  | Integer   |        | >9                |
| ClassName      | \[no]   | \[no]  | Character | 32     | x(32)             |
| ClassValue     | \[no]   | \[no]  | Integer   |        | ->,>>>,>>9        |
| DurationDays   | \[no]   | \[no]  | Integer   |        | >9                |
| Location       | \[no]   | \[no]  | Character | 32     | x(32)             |
| StartDate      | \[no]   | \[no]  | Datetime  |        | 99/99/9999 HH:... |
| TopicType      | \[no]   | \[no]  | Character | 32     | x(32)             |


< [ ] > [ ] >> [ 50 ] Records per Page

But if changes of field are required, you can undeploy your Business component, make modifications and redeploy it again.

<page_number>83</page_number>

QAD Enterprise Platform

# Undeploy / Redeploy a Business Component

Screenshot of the QAD Enterprise Platform Business Components screen showing the "Revert to Initial" action being selected for the "Training" component.

You can undeploy your Business Component only if it was suspended.

To do this, open Business Components screen, select Training and in the Actions menu choose "Revert to Initial".

QAD logo

<page_number>84</page_number>

QAD Enterprise Platform

# Undeploy / Redeploy a Business Component

Screenshot of QAD Enterprise Platform showing a "Revert to Initial" confirmation dialog box over a Business Component configuration screen. The dialog states: "The status will be changed to 'Suspended'. To complete the revert to 'Initial' status, run the required YAB command. Are you sure you want to continue?"

You will see this warning message that the BC status will be set to Suspend.

Choose Continue.

At this point, the data table for this business component still exists in DB, but the functionality suspended.

QAD logo

<page_number>85</page_number>

QAD Enterprise Platform

# Undeploy / Redeploy a Business Component

Screenshot of PuTTY Configuration and PuTTY Security Alert windows with red arrows pointing from instructional text to specific UI elements.

Now we will need to execute some Linux commands. And we'll do that using a utility called Putty.

Run the Putty, put hostname of your environment and click Connect.

If you get the security alert as shown, click yes.

QAD logo

<page_number>

86
</page_number>

QAD Enterprise Platform

# Undeploy / Redeploy a Business Component

```bash
login as: mfg
mfg@vmlwdslab1.qad.com's password:
Last login: Thu Aug 29 05:38:46 2019 from vmlwdslab1.qad.com
[mfg@vmlwdslab1 ~]$ cd /dr01/qadapps/systest
[mfg@vmlwdslab1 systest]$
```

Login as user: mfg
Password is: qad

Then type:
cd /dr01/qadapps/systest
And hit \<enter>

This moves our session to the correct directory.

<page_number>

87
</page_number>

QAD Enterprise Platform

# Undeploy / Redeploy a Business Component

```bash
$ yab database-extension-obsolete-schema

    database-extension-obsolete-schema (1 task)          [APPLY]
------------------------------------------------------------------------------
1/1 database-extension-obsolete-schema                   UPDATED (0.243 s)
------------------------------------------------------------------------------

BUILD SUCCESSFUL (1.018 s)
[mfg@vmlwdslab1 systest]$
```

Yab commands to execute in order to remove the actual data table associated with the Business Component:

`yab stop`

`yab database-extension-obsolete-schema`

`yab start`

<page_number>

88
</page_number>

QAD Enterprise Platform

# Undeploy / Redeploy a Business Component

Screenshot of QAD Enterprise Platform interface showing a Business Component named "Training" in "Initial" status.

After the commands on the previous page, the Business Component will be in the Initial state.

QAD logo

<page_number>89</page_number>

QAD Enterprise Platform

# Undeploy / Redeploy a Business Component

| Physical Field | Formula | Lookup | Data Type | Length | Format            |
| -------------- | ------- | ------ | --------- | ------ | ----------------- |
| Capacity       | \[no]   | \[no]  | Integer   |        | >9                |
| ClassName      | \[no]   | \[no]  | Character | 32     | x(32)             |
| ClassValue     | \[no]   | \[no]  | Integer   |        | ->,>>>,>>9        |
| DurationDays   | \[no]   | \[no]  | Integer   |        | >9                |
| Location       | \[no]   | \[no]  | Character | 32     | x(32)             |
| StartDate      | \[no]   | \[no]  | Datetime  |        | 99/99/9999 HH:... |
| TopicType      | \[no]   | \[no]  | Character | 34     | x(34)             |


< [ ] > [ ] >> [ 50 ] Records per Page

You can make any schema changes or delete Business Component in case of need.

<page_number>

90
</page_number>

QAD Enterprise Platform

# Undeploy / Redeploy a Business Component

**Deployment**

Screenshot of the Deployment section in QAD Enterprise Platform showing the Data Store URI field, Import Data checkbox, and Deploy button.

Scroll down to the bottom of the page and select the same Data Store as you did when we deployed this Business Component previously.

Then click Deploy.

QAD logo

<page_number>91</page_number>

QAD Enterprise Platform

# Undeploy / Redeploy a Business Component

Screenshot of QAD Enterprise Platform showing an empty Training form with a red arrow pointing to the empty list, indicating data loss.

Pay attention, that we lost the content data when we executed the YAB command:

`database-extension-obsolete-schema`

It happened because DB table was physically removed.

If you want to save your data, Export records before the Undeploy.

<page_number>

92
</page_number>

QAD logo

# QAD Inc.

<page_number>

93
</page_number>