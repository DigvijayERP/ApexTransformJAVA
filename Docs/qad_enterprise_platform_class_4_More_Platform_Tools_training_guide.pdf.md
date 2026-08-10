QAD logo

# QAD

## Class 4: QAD Enterprise Platform - More Platform Tools

By Don Springer

QAD Enterprise Platform

# Topics

* Lookup

* Conditional Styling

* Secondary Indexes & Initial Sorting

* Adding of new Browses and Views

* Predefined Search

* KPIs & Action Center

* Exporting and Installing Apps

QAD logo

<page_number>2</page_number>

# Lookups

QAD logo

<page_number>3</page_number>

QAD Enterprise Platform

# Lookup Definition

Screenshot of the Training Room screen in QAD Enterprise Platform showing a list of records and a data entry form for Class Name, Location, Room Name, Start Date, and End Date.

From the menu search open the Training Room screen. Pay attention that you are able to create records from this view.

Let’s add a lookup to the Class Name field to allow choosing from the available Training records.

QAD logo

<page_number>4</page_number>

QAD Enterprise Platform

# Lookup Definition

| Field URI                                                                                  | Reference | Browse URI                                          | App                     |
| ------------------------------------------------------------------------------------------ | --------- | --------------------------------------------------- | ----------------------- |
| urn:field:com.extensions.officesupport.Offices.IOffices:Offices.Address                    |           | urn:browse:mfg:ad057                                | OfficeSupport           |
| urn:field:com.qad.advancedselfbilling.asb.ISelfBillInvoice:SelfBillInvoice.BillToCustomer  |           | urn:browse:mfg:cm007                                | advancedselfbilling-... |
| urn:field:com.qad.advancedselfbilling.asb.ISelfBillInvoice:SelfBillInvoice.CreditTermsCode |           | urn:browse:bebrowse:com.qad.erp.base.creditTerms    | advancedselfbilling-... |
| urn:field:com.qad.advancedselfbilling.asb.ISelfBillInvoice:SelfBillInvoice.CurrencyCode    |           | urn:browse:bebrowse:com.qad.erp.base.currencies     | advancedselfbilling-... |
| urn:field:com.qad.advancedselfbilling.asb.ISelfBillInvoice:SelfBillInvoice.DaybookSetCode  |           | urn:browse:bebrowse:com.qad.erp.base.daybookSets    | advancedselfbilling-... |
| urn:field:com.qad.advancedselfbilling.asb.ISelfBillInvoice:SelfBillInvoice.InvoiceLanguage |           | urn:browse:bebrowse:com.qad.erp.base.languages      | advancedselfbilling-... |
| urn:field:com.qad.advancedselfbilling.asb.ISelfBillInvoice:SelfBillInvoice.Project         |           | urn:browse:bebrowse:com.qad.erp.financials.projects | advancedselfbilling-... |
| urn:field:com.qad.advancedselfbilling.asb.ISelfBillInvoice:SelfBillInvoice.SiteCode        |           | urn:browse:bebrowse:com.qad.erp.base.sites          | advancedselfbilling-... |
| urn:field:com.qad.advancedselfbilling.asb.ISelfBillInvoice:SelfBillInvoice.SoldToCustomer  |           | urn:browse:mfg:cm007                                | advancedselfbilling-... |
| urn:field:com.qad.advancedselfbilling.asb.ISelfBillInvoice:SelfBillInvoice.TaxClass        |           | urn:browse:bebrowse:com.qad.erp.tax.taxClasss       | advancedselfbilling-... |


Via the Main Menu find the Lookup Definition page.

<page_number>5</page_number>

QAD Enterprise Platform

# Lookup Definition

Screenshot of the Lookup Definition interface in QAD Enterprise Platform showing fields for Field URI, Field Label, Reference, App, App URI, and Namespace under the Main section, and Browse URI, Browse Label, Result Field, Search Field, and Search Field Operator under the Browse section.

Click New and select field.

QAD logo

<page_number>

6
</page_number>

QAD Enterprise Platform

# Lookup Definition

Screenshot of a software interface showing a "Fields" lookup dialog with advanced search filters applied. The filters include "Field URI contains ClassName" and "Business Compo... contains TrainingRoom".

QAD logo

Use filters, they could be much helpful.

<page_number>7</page_number>

QAD Enterprise Platform

# Lookup Definition

Screenshot of the Fields lookup window in QAD Enterprise Platform showing a filtered search for "ClassName" within the "Trainingroom" Business Component.

QAD logo

Select ClassName field which was found after the filtering.

<page_number>8</page_number>

QAD Enterprise Platform

# Lookup Definition

urn:field:com.extensions.training.TrainingRoom.ITrainingRoom:TrainingRoom.Class
Field URI

Screenshot of the Lookup Definition interface in QAD Enterprise Platform, showing the Main and Browse sections. An arrow points from a callout box to the Browse URI field.

Now select an appropriate Browse for lookup.

<page_number>

9
</page_number>

QAD Enterprise Platform

# Lookup Definition

Screenshot of QAD Developer interface showing a Training browse screen on the left and browser developer tools Network tab on the right. An arrow points from a "Refresh" icon in the application to a "Refresh action" label. Another arrow points from a "browseId" value in the Network payload (urn:browse:bebrowse:com.extensions.training.training) to a "BwoesID" label.

<page_number>10</page_number>

QAD Enterprise Platform

# Lookup Definition

Screenshot of Resource lookup window showing a search result for a training browse URI

QAD logo

Select the appropriate record.

<page_number>11</page_number>

QAD Enterprise Platform

# Lookup Definition

Screenshot of Browse configuration showing Browse URI, Browse Label, Result Field, and Search Field inputs.

Now select Result and Search fields.

In our case we should select Class Name for both.

Screenshot of the Fields selection dialog showing a list of available fields including Class Name, Location, Description, Student Count, Average Score, Start Date, and Duration Days.

QAD logo

<page_number>12</page_number>

QAD Enterprise Platform

# Lookup Definition

**Additional Result Fields**

Screenshot of Additional Result Fields configuration in QAD Enterprise Platform showing a table with columns Field and Target. The Field is set to training.location and the Target is set to TrainingRoom_locationAutoField1.

Let’s also add additional result field.

Set training.location as Field and TrainingRoom_locationAutoField1 as Target.

QAD logo

<page_number>13</page_number>

urn:field:com.extensions.training.TrainingRoom.ITrainingRoom:TrainingRoom.ClassName
Field URI

QAD Enterprise Platform

# Lookup Definition

Click Save to create Lookup.

Screenshot of Lookup Definition interface showing Main, Browse, Search Conditions, and Additional Result Fields sections.

### Main

**Field URI**: urn:field:com.extensions.training.TrainingRoom.ITrainingRoom:TrainingRoom.ClassName
**Field Label**: Class Name
**Reference**:

### Browse

**Browse URI**: urn:browse:bebrowse:com.extensions.training.training
**Browse Label**: Training
**Result Field**: training.className
**Search Field**: training.className
**Search Field Operator**: greater or equal to

### Search Conditions

* New Delete More

| Field Name | Operator | Value | Type |
| ---------- | -------- | ----- | ---- |


50 Records per Page

### Additional Result Fields

* New Delete More

| Field             | Target                           |
| ----------------- | -------------------------------- |
| training.location | TrainingRoom\_locationAutoField1 |


QAD logo

<page_number>14</page_number>

QAD Enterprise Platform

# Lookup Definition

Now, open or refresh the Training Room page.

Screenshot of the Training Room page showing a lookup icon in the Class Name field and an arrow pointing to it from the instructional text.

You will find a lookup icon in the Class Name field.

Use it to select class Name and note that Location value was populated automatically.

QAD logo

<page_number>

15
</page_number>

QAD Enterprise Platform

QAD logo

# Lookup Relation vs Lookup Definition

### Lookup Relation

**Goal:** to provide relation between two business components

**Lookup icon:** useful side-effect

**Form:** could not contain field with added relation

VS.

### Lookup Definition

**Goal:** to provide simple access to browse with existing records

**Lookup icon:** goal of adding

**Form:** will always contain field with added lookup

<page_number>16</page_number>

# Conditional Styling

QAD logo

<page_number>17</page_number>

QAD Enterprise Platform

# Adding Conditional Styling

Screenshot of the QAD Enterprise Platform interface showing the Country Industries Build Form screen with Form Layout Properties for the Sales in Millions column.

Go to the Business Components screen and open CountryIndustries.

Navigates to the Form panel and click "Edit Form".

Select Sales in Millions column.

Then find Conditional Styling in Form Layout Properties section and click the Gear.

QAD logo

<page_number>18</page_number>

QAD Enterprise Platform

# Adding Conditional Styling

Build Form > Conditional Styling [x]

## Conditional Styling

| salesInMillions | Sales in Millions |
| --------------- | ----------------- |
| Field Name      | Display Label     |


**Styles**

**Styles**
Style Type: [Background Color [v]]

[+ New] [Edit] [Delete]

| Condition | Preview |
| --------- | ------- |
|           |         |


[OK] [Cancel]

Screenshot of the Conditional Styling panel with a callout box pointing to the New button. The callout text reads: "You have reached the Conditional Styling Panel. Click New."

<page_number>19</page_number>

QAD Enterprise Platform

# Adding Conditional Styling

Screenshot of the Styles configuration window in Build Form > Conditional Styling, showing field name salesInMillions, display label Sales in Millions, and a condition set for Sales in Millions greater than 800 with a Green background color style.

Select "greater than" and enter 800. Choose Green color from the dropdown and click Ok.

Select "greater than" and enter 300. Choose Orange color and click Ok.

Select "less than or equal to" and enter 300. Choose Red color and click Ok.

<page_number>

20
</page_number>

QAD Enterprise Platform

# Adding Conditional Styling

Screenshot of the Conditional Styling configuration window in QAD Enterprise Platform, showing field "salesInMillions" with three background color conditions: greater than "800" (green), greater or equal to "300" (blue), and less than "300" (red).

This is an expected result of configuration.

You can click OK.

Then click Save and Close on the Build Form Page.

<page_number>

21
</page_number>

QAD Enterprise Platform

# Adding Conditional Formatting

Now go to the menu and choose Countries.

**Country Industries**

Then open the country where you previously added Country Industries.

| Industry  | Business Count | Sales in Millions | Exporter |
| --------- | -------------- | ----------------- | -------- |
| Beer      | 35             | 300               | \[no]    |
| Chocolate | 40             | 850               | \[no]    |
| Cookies   | 12             | 250               | \[no]    |


Your display should appear as shown.

You may need to refresh a page if you don’t immediately see the result as shown.

<page_number>

22
</page_number>

# Secondary Index and Initial Sorting

QAD logo

<page_number>23</page_number>

QAD Enterprise Platform

# Add Initial Sorting

Training | <No Stored View> ▾ | + New | Edit | More ▾
[Class Name starts with      ▾] [Search]

| Class Name  | Location      | Start Date         | Student Count | Duration Days |
| ----------- | ------------- | ------------------ | ------------- | ------------- |
| Purchasing  | Chicago       | 10/10/2023 3:33 PM | 9             | 10            |
| Sales Order | Santa Barbara | 10/12/2023 1:19 PM | 5             | 5             |


QAD logo

We will add default sorting into the Training browse. Start Date column should show newest trainings first.

<page_number>24</page_number>

QAD Enterprise Platform

# Add Secondary Index to Training

## Indexes

Screenshot of the Indexes management screen showing a table with idx_PK as the Primary Index and a "New" button highlighted by a red arrow.

QAD logo

To avoid performance degradation If number of training records is huge, we should add one more index into Training component.

<page_number>25</page_number>

QAD Enterprise Platform

# Add Secondary Index to Training

## Main

**Index**: StartDate_index
**Description**: StartDate_index
**Unique**: [ ]

## Fields

* Select Delete More

| Physical Field | Order | Direction |
| -------------- | ----- | --------- |
|                |       |           |


Create new index: StartDate_index.

In the Fields panel click Select to choose the fields for the index.

QAD logo

<page_number>26</page_number>

QAD Enterprise Platform

# Add Secondary Index to Training

Screenshot of the Fields configuration interface showing the StartDate field with Order 0 and Direction Descending.

Add StartDate field and set Direction as Descending.

Descending order will show highest values first, but this can be reversed in the View.

Click Save & Close in indexes.

You will get a warning that a yab command is required.

QAD logo

Save the Business Component.

<page_number>27</page_number>

QAD Enterprise Platform

# Add Secondary Index to Training

```bash
yab stop database-extension-index-rebuild
yab start
```

Via the Putty execute next two yab commands exactly as shown on the left.

QAD logo

<page_number>

28
</page_number>

QAD Enterprise Platform

# Add Initial Sorting

## Browses

Screenshot of the Browses panel in QAD Enterprise Platform showing a table with a row for "Training" and action buttons like New, Add Child, Edit, Delete, Details, More, and Preview. A red circle highlights the Edit button, with a red arrow pointing to a text box below.

Then scroll down to Browses panel, select view and click Edit or Details.

QAD logo

<page_number>29</page_number>

QAD Enterprise Platform

# Add Initial Sorting

**Initial Sort**

Screenshot of the Initial Sort panel in QAD Enterprise Platform showing fields for Field, Display Label, Order, Direction, Warning, and Business Component. A red arrow points from the "New" button to a text box containing instructions.

Navigate to Initial Sort panel and click New.

Set Direction to Descending and Order to 1.

Click lookup in Field textbox.

QAD logo

<page_number>30</page_number>

# QAD Enterprise Platform

# Add Initial Sorting

Screenshot of Sortable Fields configuration window in QAD Enterprise Platform

From the list with indexes and indexed fields select StartDate.

QAD logo

<page_number>31</page_number>

QAD Enterprise Platform

# Add Initial Sorting

## Initial Sort

* New      Delete More ▼

| Field       | Display Label | Order | Direction    | Warning | Business Component |
| ----------- | ------------- | ----- | ------------ | ------- | ------------------ |
| StartDate Q | Start Date    | 1     | Descending ▼ |         | Training           |


« ‹ › » 50 ▼ Records per Page

Save view.

Close modal window and save business component.

QAD logo

<page_number>32</page_number>

# QAD Enterprise Platform

# Add Initial Sorting

Screenshot of the Training screen showing a browse list with columns for Class Name, Location, Description, Student Count, Average Score, Start Date, Duration Days, Topic Type, and Area. The Start Date column has a descending sort arrow.

Navigate to Training screen.

Pay attention that records in the browse initially sorted by Start Date.

QAD logo

<page_number>33</page_number>

# Add New Browse and View

QAD logo

<page_number>34</page_number>

QAD Enterprise Platform

# Add new Browse and View for Countries

Screenshot of the Countries browse screen in QAD Enterprise Platform showing a search for country starting with "#BE" and a result for Belgium.

As an example, we will build an “Industries per Country” browse

QAD logo

<page_number>35</page_number>

QAD Enterprise Platform

# Add new Browse and View for Countries

Screenshot of the Business Components screen showing a search for "countries" with the Countries component selected.

Go to Business Components screen and find Countries

Click Edit.

QAD logo

<page_number>

36
</page_number>

QAD Enterprise Platform

# Add new Browse for Countries

## Browses

Screenshot of the Browses panel in the QAD Enterprise Platform interface, showing a table with columns for Name, Browse URI, App, and App URI. A red arrow points from a text box at the bottom to the "+ New" button in the toolbar.

Find Browses panel and click “New”.

QAD logo

<page_number>37</page_number>

QAD Enterprise Platform

# Add new Browse for Countries

Screenshot of the "Add new Browse" form in QAD Enterprise Platform showing fields for Browse Label, Browse URI, Description, App, and App URI. A red arrow points to the Browse Label field.

Enter Browse Label “Industries per Countries”.

QAD logo

<page_number>38</page_number>

QAD Enterprise Platform

# Add new Browse for Countries

## Fields

Screenshot of the Fields configuration panel in QAD Enterprise Platform showing a list of country-related fields with checkboxes for selection.

In Fields panel unselect all fields except CountryCode and CountryDescription.

Then click Select button.

<page_number>

39
</page_number>

QAD Enterprise Platform

# Add new Browse for Countries

Screenshot of the QAD Enterprise Platform interface showing the "Select Relationship" screen for CountryEX. A table lists "Countries" with its label and URI. A red arrow points from the "Countries" row to a text box.

Leave selection on Countries component and click Continue.

QAD logo

40

QAD Enterprise Platform

# Add new Browse for Countries

Screenshot of Select Fields dialog in QAD Enterprise Platform showing a list of fields including CountryID, CountryType, CurrencyCode, CurrencyID, and CustomCombo0. The CurrencyCode field is selected with a checkmark.

Click the check box near with CurrencyCode fields.

Click OK.

QAD logo

<page_number>41</page_number>

QAD Enterprise Platform

# Add new Browse for Countries

Screenshot of the Select Relationship screen in QAD Enterprise Platform showing a table of relationships for the Countries business component. A red arrow points to the CountryIndustries relationship row.

Click select on more time.

Select CountryIndustries and hit Enter.

QAD logo

<page_number>42</page_number>

QAD Enterprise Platform

# Add new Browse for Countries

Screenshot of Select Fields dialog box showing a table of field names like BusinessCount, CountryCode, Exporter, Industry, SalesInMillions, and [Exists] with their respective display labels, data types, and formats.

Select BusinessCount, Industry, SalesInMillions and Exporter fields.

Then click Save & Close at the bottom of the Views Page.

Then click Save at the Bottom of the Business Component Page.

QAD logo

<page_number>

43
</page_number>

QAD Enterprise Platform

# Add new Browse for Countries

**Fields**

For optimal performance, select **50** or fewer columns. When the browse is run, only the first **20** columns display by default.

More [dropdown] | + Select | + New Conditional Field | Edit Conditional Field | Configure Joins

| Select | Field              | Field Label       | Display Label     | Physical Field     | Sortable |
| ------ | ------------------ | ----------------- | ----------------- | ------------------ | -------- |
| \[yes] | CountryCode        | mfg-COUNTRY       | Country           | CountryCode        | \[yes]   |
| \[yes] | CountryDescription | mfg-DESCRIPTION   | Description       | CountryDescription | \[yes]   |
| \[yes] | CurrencyCode       | mfg-CURRENCY      | Currency          | CurrencyCode       | \[yes]   |
| \[yes] | BusinessCount      | Business Count    | Business Count    | BusinessCount      | \[yes]   |
| \[yes] | Exporter           | Exporter          | Exporter          | Exporter           | \[yes]   |
| \[yes] | Industry           | Industry          | Industry          | Industry           | \[yes]   |
| \[yes] | SalesInMillions    | Sales in Millions | Sales in Millions | SalesInMillions    | \[yes]   |


<< < > >> 50 [dropdown] Records per Page 1 - 7 of 7

QAD logo

Once you save new browse, you will have next list of fields.
Close Close.

<page_number>44</page_number>

QAD Enterprise Platform

# Add new Browse for Countries

Screenshot of the "Configure Column Order" dialog for Industries per Countries in the QAD Enterprise Platform. The dialog shows a table header with columns: Country, Description, Industry, Business Count, Sales in Millions, Currency, and Exporter. A message in the center says "Drag and drop columns to configure column order."

QAD logo

Configure next order of columns.

<page_number>45</page_number>

QAD Enterprise Platform

# Add new View for Countries

Screenshot of the Views panel in QAD Enterprise Platform showing a table with columns View Label, Description, Type, and Eligible for Menu. A red arrow points to the "+ New" button.

Now, in the Views panel. You can add as many Views as you need.

Click “New”.

QAD logo

<page_number>46</page_number>

QAD Enterprise Platform

# Add new View for Countries

Screenshot of the QAD Enterprise Platform interface showing the configuration of a new View for Countries, with callouts pointing to specific fields.

Enter View Label “Industries per Countries ”.

Unclick options Allow New, Allow Edit and Allow Delete.

Select earlier created browse.

Save View and click Close.

<page_number>47</page_number>

QAD Enterprise Platform

# Add new View for Countries

Screenshot of QAD Menu Search showing "industries" search and "Industries per Countries" result

Now go to Menu Search, and type “Industries”.

Choose “Industries per Countries”.

QAD logo

<page_number>

48
</page_number>

QAD Enterprise Platform

# Add new View for Countries

Screenshot of the QAD Enterprise Platform interface showing a table titled "Industries per Countries" with multiple entries for Belgium (#BE) due to a many-to-one relation extension. Red arrows highlight the repeated entries and the "Open" button.

Notice that Belgium (#BE) appears 3 times. It happens because we added a field from the extension with many to one relation.

Also pay attention that Open button is displayed instead of New and Edit buttons.

<page_number>49</page_number>

# Predefined Search

QAD logo

<page_number>50</page_number>

QAD Enterprise Platform

# Add predefined search

## Browses

Screenshot of the Browses configuration screen showing a table with columns Name, Browse URI, App, and App URI. An arrow points from the text box below to the Edit button.

To add the predefined search, scroll to Browses.

Click Edit or Details.

QAD logo

<page_number>51</page_number>

QAD Enterprise Platform

# Add predefined search

Screenshot of the Predefined Search Criteria panel in the QAD Enterprise Platform interface, showing options for "Show in Advanced Search" checkbox, and buttons for "Include Field", "Include Operator", "Include Variable", and "Check Syntax" above a text entry area.

Scroll to Predefined Search Criteria panel.

QAD logo
<page_number>

52
</page_number>

QAD Enterprise Platform

# Add predefined search

Screenshot of Predefined Search Criteria interface in QAD Enterprise Platform

Use include Field and Include Operator buttons to add next condition:
_com_extensions_training_CountryIndustries.Industry isNotNull

Then save view again.

QAD logo

<page_number>53</page_number>

QAD Enterprise Platform

# Add predefined search

Screenshot of Industries per Countries browse showing filtered results

Now, navigate back to Industries per Country and refresh the browse.

You can see that all records where Industry value is null were filtered out.

QAD logo

<page_number>54</page_number>

# KPIs

QAD logo

<page_number>55</page_number>

# QAD Enterprise Platform

# Build a KPI

Screenshot of QAD Enterprise Platform interface showing the KPIs management screen with a search menu open and an arrow pointing to the "KPIs" menu item.

QAD logo

Select KPIs from the menu.

<page_number>56</page_number>

# QAD Enterprise Platform

# Build a KPI

Screenshot of the KPIs Factory View interface showing a list of KPIs with columns for KPI name, Data Source Type, Data Source Label, Data Source, Active status, KPI Type, and Auto Refresh. A red arrow points from the "Click New." text box to the "+ New" button in the toolbar.

Click New.

QAD logo

<page_number>57</page_number>

# QAD Enterprise Platform

# Build a KPI

Screenshot of the KPI configuration screen in QAD Enterprise Platform showing fields for KPI Name, Data Source Type, Data Source, and other settings.

1. Enter “Training Results” as the KPI Name.

2. Click the “Select” button and select Training for Data Source.

QAD logo

<page_number>58</page_number>

# QAD Enterprise Platform

# Build a KPI

KPIs > Select Browse Data Source

Screenshot of Data Source selection screen in QAD Enterprise Platform

1. Select Data Source with description: Training.

2. Then, click OK.

QAD logo

<page_number>59</page_number>

# QAD Enterprise Platform

# Build a KPI

**Training Results**
KPI

**Yes**
Active

| Main | Browse | Domains & Entities | Fields | Refresh Options | Visuals | Additional Details | \[gear icon] |
| ---- | ------ | ------------------ | ------ | --------------- | ------- | ------------------ | ------------ |


### Main

**KPI**: Training Results
**Filter by Current Workspace**: [ ]
**Data Source Type**: Browse [dropdown]
**Saved To**: Configuration Data
**Data Source**: urn:browse:bebrowse:com.extensions.training.... [Select]
**Visual Type**: Composer
**Data Source Label**: Training
**Active**: [x]
**KPI Type**: Current Data [dropdown]

### Browse

[Configure] Configure browse columns and search criteria.
**Criteria**: Configure to see criteria and lines returned.

### Domains & Entities

Only data from selected Domains or Entities is made available.
**Browse By Domain**: [ ]
**Browse By Entity**: [ ]

### Fields

**Group Data**: [ ] **Group Dates By**: Day [dropdown]
**Active Fields**: 0 **Max**: 20

[Save] [dropdown] [Cancel]

Now Click the Configure button for the Browse.

QAD logo

<page_number>60</page_number>

QAD Enterprise Platform

# Build a KPI

KPIs > Configure Browse Data Source

**Training** <No Stored View> + New Edit More

```
 Search
```

| Class Name    | Location        | Description | Start Date         | Student Count | Duration Days |
| ------------- | --------------- | ----------- | ------------------ | ------------- | ------------- |
| *Sales Order* | *Santa Barbara* |             | 10/12/2023 1:19 PM | 5             | 5             |
| Purchasing    | Chicago         |             | 10/10/2023 3:33 PM | 9             | 10            |


QAD logo

Configure the Browse: just accept the default and click Ok.

<page_number>61</page_number>

# QAD Enterprise Platform

# Build a KPI

Screenshot of the KPI builder interface showing the Fields and Refresh Options sections. The Fields table has checkboxes for Active fields, including Average Score, Class Name, and Student Count which are selected.

In the Fields section leave selection for fields which will be used for visualization.

In our case we will need:
Class Name
Average Score
Student Count.

<page_number>62</page_number>

**QAD Enterprise Platform**

# Build a KPI

**Fields**

Group Data [ ] Group Dates By [Day]
Active Fields [3] Max 20

More ▾

| Active ▾1 | Field Label ▴ | Data Type ⇌ | Case ⇌        | Field Format ⇌ | Field ⇌                                       |
| --------- | ------------- | ----------- | ------------- | -------------- | --------------------------------------------- |
| \[yes]    | Average Score | Number      |               |                | training.averageScore                         |
| \[yes]    | Class Name    | Text        | No Conversion |                | training.className                            |
| \[yes]    | Student Count | Number      |               |                | training.studentCount                         |
| \[no]     | Area of Study | Text        | No Conversion |                | training.areaOfStudy                          |
| \[no]     | Capacity      | Number      |               |                | training.capacity                             |
| \[no]     | Class Value   | Number      |               |                | training.classValue                           |
| \[no]     | Description   | Text        | No Conversion |                | joinTable\_9c68b381192b45a.countryDescription |


« ‹ › » [50] Records per Page

**Refresh Options**

Auto Refresh [x]
Refresh Rate [Daily]
Allow Manual Refresh [x]

Be sure to check “Allow Manual Refresh”.

Click Save.

If you receive an error related to auto-refresh, uncheck the Auto-Refresh checkbox and click Save again.

<page_number>63</page_number>

# QAD Enterprise Platform

# Build a KPI

More ▼

| Active ¹ | Field Label   | Data Type | Case          | Fi |
| -------- | ------------- | --------- | ------------- | -- |
| \[yes]   | Average Score | Number    |               |    |
| \[yes]   | Class Name    | Text      | No Conversion |    |
| \[yes]   | Student Count | Number    |               |    |
| \[no]    | Area of Study | Text      | No Conversion |    |
| \[no]    | Capacity      | Number    |               |    |
| \[no]    | Class Value   | Number    |               |    |
| \[no]    | Description   | Text      | No Conversion |    |


« < > » 50 ▼ Records per Page

**Refresh Options**

* Auto Refresh [x]
* Refresh Rate [Daily ▼]
* Allow Manual Refresh [x]

After Saving scroll to Visuals and click New.

**Visuals**

* New Edit Delete Details More ▼

| Visual | Chart Type | Data Field |
| ------ | ---------- | ---------- |


64

QAD Enterprise Platform

# Build a KPI

Screenshot of the "Select Visual Type" dialog in QAD Enterprise Platform, showing options like Line Trend, List Filter, Maps, Packed Bubbles, Pie, Pivot Table, and Table. A red arrow points to the "Pie" option.

First choose a Visualization.

Scroll down the list and select “Pie”.

<page_number>

65
</page_number>

**QAD Enterprise Platform**

# Build a KPI

Screenshot of the QAD Enterprise Platform KPI builder interface showing a pie chart and a "Size" configuration pop-up window. The pop-up has "Student Count" selected with the "Sum" aggregation. A legend for "CLASS NAME" shows "Purchasing", "Sales Order", and "test".

Click on Group and change a default selection to Class Name.

Click on Size and change Volume to Student Count.

<page_number>66</page_number>

**QAD Enterprise Platform**

# Build a KPI

The display will immediately change to show the Class Name as the label, and the Student Count as the value.

| Class Name  | Student Count (Sum) |
| ----------- | ------------------- |
| Purchasing  | 9.000 (56.25%)      |
| Sales Order | 5.000 (31.25%)      |
| test        | 2.000 (12.5%)       |


Screenshot of a pie chart in the QAD Enterprise Platform interface showing student count by class name.

<page_number>67</page_number>

QAD Enterprise Platform

# Build a KPI

| CLASS NAME  | Value (Percentage) |
| ----------- | ------------------ |
| Purchasing  | 9.000 (56.25%)     |
| Sales Order | 5.000 (31.25%)     |
| test        | 2.000 (12.5%)      |


Screenshot of a pie chart in the QAD Enterprise Platform interface showing data for Purchasing, Sales Order, and test. An annotation box with a red arrow pointing to the save icon says "Now save the Visual."

<page_number>

68
</page_number>

QAD Enterprise Platform

# Build a KPI

Screenshot of the QAD Enterprise Platform interface showing a "Save As Options" dialog box over a pie chart titled "Training Results". The dialog has fields for "Default Title" and "Visual Name", both filled with "Training Results", and buttons for "Cancel" and "Save". The pie chart shows data grouped by "Class Name" with slices for "Stamping Machine Maintenance", "Laser Cutter Maintenance", "Purchasing", and "Sales Order".

Enter the Visual Name.

Then Click the Save.

<page_number>69</page_number>

QAD Enterprise Platform

# Build a KPI

Screenshot of the "Select Visual Type" dialog in QAD Enterprise Platform, showing options like Arc Gauge, Bars, Bars: Histogram, Bars: Multiple Metrics, Box Plot, Bullet Gauge, Combo Chart, Donut, and Floating Bubbles. A red arrow points to the "Bars" option.

Create one more diagram.

This time select Bars type.

<page_number>

70
</page_number>

# QAD Enterprise Platform

# Build a KPI

KPIs > Visuals > Visuals

| Class Name  | Average Score (Sum) |
| ----------- | ------------------- |
| Purchasing  | 44.000              |
| Sales Order | 43.000              |
| test        | 50.000              |


Group: Class Name Color: Average Score (Sum)

Click on Group and change a default selection to Class Name.

Click on Metric and change Volume to Average Score.

71

71

**QAD Enterprise Platform**

# Build a KPI

KPIs > Visuals > Visuals

| Class Name  | Average Score (Sum) |
| ----------- | ------------------- |
| Purchasing  | 45                  |
| Sales Order | 44                  |
| test        | 50                  |


Now save the Visual.

<page_number>72</page_number>

# Action Center

QAD logo

<page_number>73</page_number>

QAD Enterprise Platform

# Build an Action Center

Screenshot of QAD Enterprise Platform interface showing the Action Centers menu with "New Action Center" selected.

Add your own Action Center!

Click the Bar Chart Icon, and choose: "New Action Center".

QAD logo

<page_number>74</page_number>

QAD Enterprise Platform

# Build an Action Center

Screenshot of "New Action Center" dialog box with "Training & Students" entered in the Name field

Name new Action Center as “Training & Students”.

QAD logo

<page_number>75</page_number>

QAD Enterprise Platform

# Build an Action Center

Screenshot of QAD Enterprise Platform interface showing the KPI selection menu with an arrow pointing from the Bar Chart icon to the "Training & Students" option.

Click the Bar Chart Icon, and choose:

Training & Students (you may need to scroll a bit).

76

QAD Enterprise Platform

# Build an Action Center

Screenshot of QAD Enterprise Platform interface showing the "Add Visual" and "Place Existing Visual" menu options.

Choose Add Existing Visual on the menu on the right.

Click the plus Icon if you do not see the menu choices.

QAD logo

<page_number>77</page_number>

QAD Enterprise Platform

# Build an Action Center

Screenshot of the "Select a Visual" dialog box in the QAD Enterprise Platform, showing a list of data sources including "Training Results" with a red arrow pointing to it.

In the search field type “Training Results”, and this should find the KPI you just created, or you can see it right on the list.

Click on the found visual.

<page_number>

78
</page_number>

QAD Enterprise Platform

# Build an Action Center

Screenshot of QAD Action Center showing a pie chart and a bar chart visualization for Training & Students data.

You can create multiple Visualizations from the same KPI and add Visualizations from other KPIs. Arrange them for best usability in each case.

QAD logo

<page_number>

79
</page_number>

# Exporting and Installing App

QAD logo

<page_number>80</page_number>

QAD Enterprise Platform

# Exporting, Packaging and Installing an App

Any App created in QAD Enterprise Platform can be Exported, Packaged, and then Installed into another environment

* Export and Package App from DEVL and install it into TEST

* Install same package into PROD after the testing

* Update an existing app with a newer version

* Create app just a backup

Process is easy and it takes only a few minutes

QAD logo
<page_number>

81
</page_number>

QAD Enterprise Platform

# Exporting, Packaging and Installing an App

Screenshot of the QAD Enterprise Platform Apps interface showing the Training app selected and the Actions menu open with the Package option highlighted.

Open Apps using the main menu search.

Search for the Training App that we created earlier.

With Training selected click on Actions, and you will find the option to package your App.

Click Package.

QAD logo

<page_number>82</page_number>

QAD Enterprise Platform

# Exporting, Packaging and Installing an App

Apps > Package

Screenshot of the Package screen in QAD Enterprise Platform showing versioning fields: Major Version 1, Minor Version 0, Patch Version 0, Build 0, Version 1.0.0.0, and Package com-extensions-training-1.0.0.0

Note that the field values are pre-populated.

You have the option to update the versioning information depending upon your company practices.

Package File

Once you click submit, the App will be packaged and a link sent to your Inbox

Information icon The package file will be sent to your inbox.

QAD logo

<page_number>

83
</page_number>

QAD Enterprise Platform

# Exporting, Packaging and Installing an App

Screenshot of QAD Inbox showing a notification for "OS Script Processing: Create app package" with a Download link. See that the notification of successfully creating the package includes a download link so that you can download a copy of the package directly from the Inbox.

Screenshot of browser Downloads window showing the downloaded file "com-extensions-training-1.0.0.0.zip".

QAD logo

<page_number>84</page_number>

QAD Enterprise Platform

# Exporting, Packaging and Installing an App

* With QAD Cloud environments a package is installed by QAD Cloud Admins

* Customers do not take this technical action themselves but log a request to install a given package

* These activities are carefully logged by QAD, and strictly controlled for the protection of customer environments.

* As you can see it is quite simple to generate copies of an App to be used for version control, and as backups

QAD logo

<page_number>

85
</page_number>

QAD logo

QAD Inc.

<page_number>86</page_number>