QAD logo

# QAD

## Class 7: QAD Enterprise Platform - Event Handlers

By Don Springer

logo

QAD Enterprise Platform

# Topics

* Event Handlers Overview
* Using of data from the record
* Using of data from the extension
* Using of Grids

QAD logo

logo

2

# Event Handlers Overview

Company logo

logo

<page_number>3</page_number>

**QAD Enterprise Platform**

### QAD Enterprise Platform: Event Handler Architecture

| Layer   | Component                    |
| ------- | ---------------------------- |
| Server  | Database                     |
|         | BL                           |
|         | Data Controller              |
| Browser | Model (JSON)                 |
|         | View (DOM)                   |
|         | View Controller              |
|         | TS API                       |
|         | TS handlers / Event handlers |


# What is Event Handler?

An Event Handler is a TypeScript code which is compiled into JavaScript and is saved to the database. It’s assigned to the business component, so it will be executed on the front-end side for the corresponding UI.

logo

<page_number>4</page_number>

**QAD Enterprise Platform**

# Run time order of Event Handlers

* **Primary** – primary event handler for corresponding business component. Default type for all TS handler in coded BCs.
* **Pre** – runs before Primary or coded event handler.
* **Post** – runs after Primary or coded event handler.

QAD logo

logo

# QAD Enterprise Platform

# Event handler types

QAD UI screenshot

**View TS handler:**
This is the main event handler which is reacting on page lifecycle events. This type is also needed as a starting point for other event handlers.

### Table: Class Name and Location

| Class Name  | Location      |
| ----------- | ------------- |
| Sales Order | Santa Barbara |
| Purchasing  | Chicago       |


### Table: Students

| First Name | Last Name | Score |
| ---------- | --------- | ----- |
| Moe        | Howard    | 85    |
| Joe        | Kent      | 92    |
| Lou        | Malnotti  | 95    |
| Arthur     | Treacher  | 95    |
| Bruce      | Wayne     | 90    |


logo

QAD Developer E My Developer Settings Development Logging Options Analytics 10USA, 10USACO Q Training <No Stored View> + New Delete More Sales Order View TS Handler Santa Barbara Class Name Location Class Name Location Sales Order Santa Barbara Training Students Training Room 8 Purchasing Chicago Training Class NameSales Order Topic TypeTech LocationSanta Barbara ViewForm Area of StudyDistribution Country α UNITED STATES 10 Start DateUS5/19/2026 10:41 PM handler Class Value 8 Confirm G Capacity Duration Days 5 Student Count 5 Browse Average Score 91.40 Handler Students +New Delete More First Name : Last Name : Score Moe Howard 35 Joe Kent Grid Handler 92 Lou Malnotti 95 Arthur Treacher 95 Bruce Wayne 90 > 7 50 Records per Page f 5

# QAD Enterprise Platform

# Event handler types

QAD UI screenshot

**ViewForm handler:**
This is an event handler that can act on UI events related to form elements (such as labels, input fields or buttons)

| First Name | Last Name | Score |
| ---------- | --------- | ----- |
| Moe        | Howard    | 85    |
| Joe        | Kent      | 92    |
| Lou        | Malnotti  | 95    |
| Arthur     | Treacher  |       |
| Bruce      | Wayne     | 90    |


logo

QAD Developer E My Developer Settings Development Logging Options Analytics 10USA, 10USACO Q Training <No Stored View> + New Delete More Sales Order View TS Handler Santa Barbara Class Name Location Class Name Location Sales Order Santa Barbara Training Students Training Room 8 Purchasing Chicago Training Class NameSales Order Topic TypeTech LocationSanta Barbara ViewForm Area of StudyDistribution Country α UNITED STATES 10 Start DateUS5/19/2026 10:41 PM handler Class Value 8 Confirm G Duration Days 5 Student Count 5 Browse Average Score 91.40 Handler Students +New Delete More First Name : Last Name : Score Moe Howard 35 Joe Kent Grid Handler 92 Lou Malnotti 95 Arthur Treacher 95 Bruce Wayne 90 > 7 50 Records per Page f 5

# QAD Enterprise Platform

## Event handler types

QAD interface screenshot

**ViewGrid handler:**
This type of event handlers is responsible for processing of grid events. It combines all grid events including lifecycle and controls actions.

| Class Name  | Location      |
| ----------- | ------------- |
| Sales Order | Santa Barbara |
| Purchasing  | Chicago       |


| First Name | Last Name | Score |
| ---------- | --------- | ----- |
| Moe        | Howard    | 85    |
| Joe        | Kent      | 92    |
| Lou        | Malnotti  | 95    |
| Arthur     | Treacher  |       |
| Bruce      | Wayne     | 90    |


logo

QAD Developer B My Developer Settings Development Logging Options Analytics 10USA, 10USACO Q Training <No Stored View> + New Delete More Sales Order View TS Handler Santa Barbara 0 Class Name Location Class Name Location Sales Order Santa Barbara Training Students Training Room Purchasing Chicago Training Class NameSales Order Topic TypeTech Location Distribution Santa Barbara ViewForm Area of Study Country Q 10 US UNITED STATES handler Class Value G Start Date 5/19/2026 10:41 PM Capacity 8 Confirm Duration Days 5 Student Count 5 Browse Average Score 91.40 Handler Students + New Delete More First Name : Last Name : Score Moe Howard 35 Joe Kent Grid Handler 92 Lou Malnotti 95 Arthur Treacher 95 Bruce Wayne 90 3 77 50 Records per Page f 5

# QAD Enterprise Platform

# Event handler types

QAD UI screenshot

**Browse handler:**
This event handler is responsible for browse events. It allows to execute code when browse record is selected and implement own click handlers for toolbar items, including Actions drop-down.

logo

QAD Developer E My Developer Settings Development Logging Options Analytics 10USA, 10USACO Q Training <No Stored View> + New Delete More Sales Order View TS Handler Santa Barbara Class Name Location Class Name Location Sales Order Santa Barbara Training Students Training Room 8 Purchasing Chicago Training Class Name pic lype Tech Sales Order LocationSanta Barbara ViewForm Area of StudyDistribution C Country us UNITED STATES handler Class Value 10 G Start Date 5/19/2026 10:41 PM Capacity 8 Confirm Duration Days 5 Student Count 5 Browse Average Score 91.40 4 Handler Students +New Delete More First Name : Last Name : Score Moe Howard 35 Joe Kent Grid Handler 92 Lou Malnotti 95 Arthur Treacher 95 Bruce Wayne 90 > 7 50 Records per Page f 5

# QAD Enterprise Platform

# Base Classes

* **QraViewTSHandlerWithViewFormTSHandler**
  Base class for the View TS event handlers.
* **QraViewFormTSHandlerV2**
  Base class for the ViewForm event handlers.
* **ViewGridTSHandlerV2**
  Base class for the ViewForm event handlers.
* **QraBrowseTSHandlerV2**
  Base class for the Browse event handlers.

QAD logo

logo

2 10

# Using of data from the record

Logo

logo

<page_number>11</page_number>

QAD Enterprise Platform

# Using of data from the record

### Training

**Class Name**: Sales Order
**Location**: Santa Barbara
**Country**: US UNITED STATES
**Start Date**: 5/19/2026 10:41 PM
**Duration Days**: 5
**Topic Type**: Tech
**Area of Study**: Distribution
**Class Value**: 10
**Capacity**: 8 [Confirm]
**Student Count**: 5
**Average Score**: 91.40

On the Training BC form, Route button should be disabled if StudentCount does not exceed Capacity

screenshot_from_computer

QAD logo

<page_number>12</page_number>

# QAD Enterprise Platform

# Using of data from the record

Form

Existing Form Yes [Edit Form]

**Event Handlers**

[+ New] [Delete] [Details] [More]

| Timing  | Active | Applies To | App      | App URI                         |
| ------- | ------ | ---------- | -------- | ------------------------------- |
| Primary | ✅      | Web        | Training | urn:app:com.extensions.training |


« < > » 50 Records per Page

Navigates to the Business Components screen and open Training BC.

Scroll to the Form panel.

Click Details in Event Handlers grid.

QAD logo

screenshot_from_computer

logo

screenshot_from_computer

screenshot_from_computer

<page_number>13</page_number>

**QAD Enterprise Platform**

**Using of data from the record**

| Active     | Yes      |                                                   |
| ---------- | -------- | ------------------------------------------------- |
| Timing     | Primary  | Primary event handler for this business component |
| Applies To | Web      |                                                   |
| App        | Training | urn:app:com.extensions.training                   |


# Main

Active ✅

Timing | Primary | Primary event handler for this business component

Applies To | Web

App | Training | urn:app:com.extensions.training

10 | 11 | `export class TrainingMaintHandler extends QraViewTSHandlerWithViewFormTSHandler<DTO.TrainingMaint, Trainin` 12 | `    protected createViewFormTSHandler(): TrainingFormHandler {` 13 | `        return new TrainingFormHandler(this);` 14 | `    }` 15 | 16 | `    public onBindData(eventData: EventData.QraView.BindDataEventData<any>): void {` 17 | `        this.ViewController.getViewButton("Route").IsDisabled = (this.NgData.trainings[0].studentCount <=` 18 | `    }` 19 | `}` 20 | 21 | `export class TrainingFormHandler extends QraViewFormTSHandlerV2<DTO.TrainingMaint> {` 22 | `    public onFieldChange(viewField: IViewField<any>, eventData: EventData.QraView.FieldChangeEventData<any` 23 | `        if (viewField.FieldName === "capacity") {` 24 | `            this.ViewController.getViewButton("Route").IsDisabled = (this.NgData.trainings[0].studentCount` 25 | `        }` 26 | `    }`

Red arrow pointing from line 17 to line 19

Download TrainingTSHandler.ts from materials for this lecture.

10 11 export class TrainingMaintHandler extends QraViewTSHandlerWithViewFormTSHandler\<DTO.TrainingMaint, Trainin 12     protected createViewFormTSHandler(): TrainingFormHandler { 13         return new TrainingFormHandler(this); 14     } 15 16     public onBindData(eventData: EventData.QraView\.BindDataEventData<any>): void { 17         this.ViewController.getViewButton("Route").IsDisabled = (this.NgData.trainings[0].studentCount <= 18     } 19 } 20 21 export class TrainingFormHandler extends QraViewFormTSHandlerV2\<DTO.TrainingMaint> { 22     public onFieldChange(viewField: IViewField<any>, eventData: EventData.QraView\.FieldChangeEventData\<any 23         if (viewField.FieldName === "capacity") { 24             this.ViewController.getViewButton("Route").IsDisabled = (this.NgData.trainings[0].studentCount 25         } 26     }

Copy all code from TS file.

Paste it instead of code in editor.

<page_number>14</page_number>

**QAD Enterprise Platform**

**Using of data from the record**

# Main

Active ✅ Timing Primary | Primary event handler for this business component Applies To Web App Training | urn:app:com.extensions.training

10 11 export class TrainingMaintHandler extends QraViewTSHandlerWithViewFormTSHandler\<DTO.TrainingMaint, Trainin 12 protected createViewFormTSHandler(): TrainingFormHandler { 13 return new TrainingFormHandler(this); 14 } 15 16 public onBindData(eventData: EventData.QraView\.BindDataEventData<any>): void { 17 this.ViewController.getViewButton("Route").IsDisabled = (this.NgData.trainings[0].studentCount <= 18 } 19 } 20 21 export class TrainingFormHandler extends QraViewFormTSHandlerV2\<DTO.TrainingMaint> { 22 public onFieldChange(viewField: IViewField<any>, eventData: EventData.QraView\.FieldChangeEventData\<any 23 if (viewField.FieldName === "capacity") { 24 this.ViewController.getViewButton("Route").IsDisabled = (this.NgData.trainings[0].studentCount 25 } 26 } 27

Red arrow pointing from the UI fields to the code block

Verify the “Active” checkbox.

Click Compile, and, if successful, click Save button.

Then close the editor and save Business Component.

| Button | Label   |
| ------ | ------- |
| 0      | Compile |
| 1      | Save    |
| 0      | Close   |


Compile

Save

Close

screenshot_from_manual

<page_number>15</page_number>

# QAD Enterprise Platform

# Using of data from the record

Two side-by-side form examples showing the Route button state based on Capacity value

Open Training screen and select any record.

Set Capacity which is greater than StudentCount and verify that Route button is disabled, then set Capacity which is less then StudentCount and check that Route button is became enabled.

engineering_drawing

16

QAD Enterprise Platform

# What Happens Here?

**this.NgData**

Collection of data from the selected record (data for parent record is always 0 element of this collection, e.g `this.NgData.trainings[0]`).

**onBindData** event

Event which happens each time when data from the selected record should be displayed in the form.

**onFieldChange** event

Standard event which happens each time when data in some field was changed (pay attention, that it will be triggered when modified field lost focus, not immediately)

<page_number>

17
</page_number>

# **Using of data from the extension**

Logo                                                                                                     18

logo

<page_number>18</page_number>

# QAD Enterprise Platform

# Using of data from the extension

Country Industries table and CountryExtension form

During the Save, a Known For value should be present in the list of Country Industries, otherwise an error should be displayed.

| Industry  | Business Count | Sales in Millions | Exporter |
| --------- | -------------- | ----------------- | -------- |
| Beer      | 33             | 311               |          |
| Chocolate | 40             | 805               |          |
| Cookies   | 12             | 250               |          |


logo

Country Industries + New Delete More Industry : Business Count Sales in Millions : Exporter Beer 33 311 Chocolate 40 805 Cookies 12 250 < >> 50 Records per Page CountryExtension Average Temperature 22 Average Vacation Days 22 Continent Europe Country Size Medium Known ForChocolate Population 3,000,000

19

**QAD Enterprise Platform**

**Using of data from the extension**

**⌄ Form**

⌄ Event Handlers

| Timing | Active | Applies To | App | App URI |
| ------ | ------ | ---------- | --- | ------- |
|        |        |            |     |         |


Open Business Components.

<u>Select Countries.</u>

<u>Scroll to Form and click New</u> <u>in Event Handlers grid.</u>

logo

screenshot_from_computer

screenshot_from_computer

screenshot_from_computer

<page_number>20</page_number>

# QAD Enterprise Platform

# Using of data from the extension

Main

UI configuration screenshot

```
1  module com.qad.erp.base.EventHandler.Country.ComExtensionsTraining.Maint_BEFORE {
2  "use strict";
3
4  import QraViewTSHandlerWithViewFormTSHandler = Qad.QraView.TSHandler.QraViewTSHandlerWithViewFormTSHandler;
5  import QraViewFormTSHandlerV2 = Qad.QraView.TSHandler.QraViewFormTSHandlerV2;
6  import IViewField = Qad.QraView.TSHandler.IViewField;
7  import DTO = com.qad.erp.base.EventHandler.Country.DTO;
8  import Constants = com.qad.erp.base.EventHandler.Country.Constants;
9
10 /**
11 * CountryMaintHandler : Maint TS handler class.
12 *
13 * Do not change this class name or the event handler will no longer run.
14 */
```

Pay attention that Timing
option is available now.

Select Post timing.

screenshot_from_computer

logo

21

# QAD Enterprise Platform

# Using of data from the extension

Main

Active ☐
Timing Post ▾ Runs after any other event handlers.
Applies To Web ▾
App Training urn:app:com.extensions.training

```typescript
1  module com.qad.erp.base.EventHandler.Country.ComExtensionsTraining.Maint_AFTER {
2      "use strict";
3  
4      import QraViewTSHandlerWithViewFormTSHandler = Qad.QraView.TSHandler.QraViewTSHandlerWithViewFormTSHandler;
5      import QraViewFormTSHandlerV2 = Qad.QraView.TSHandler.QraViewFormTSHandlerV2;
6      import IViewField = Qad.QraView.TSHandler.IViewField;
7      import DTO = com.qad.erp.base.EventHandler.Country.DTO;
8      import Constants = com.qad.erp.base.EventHandler.Country.Constants;
9      import Error = Qad.Common.DTO.Error;
10 
11     /**
12      * CountryMaintHandler : Maint TS handler class.
13      *
14      * Do not change this class name or the event handler will no longer run.
```

Download CountryTSHandler.ts from materials for this class.

Copy all code from TS file.

Paste it instead of the code in the editor.

engineering_drawing

22

**QAD Enterprise Platform**

**Using of data from the extension**

down arrow icon Main

| Field      | Value                                      |
| ---------- | ------------------------------------------ |
| Active     | Yes                                        |
| Timing     | Pre                                        |
| Applies To | Web                                        |
| App        | Training (urn:app:com.extensions.training) |


15 16 public onBeforeUpdate(eventData: EventData.QraView\.BeforeUpdateEventData, processEvent: (processIt?: boolean) => void): void { 17     const knownfor: string = this.NgData._com_extensions_training_CountryExtension[0].knownFor; 18     const isFound: boolean = this.NgData._com_extensions_training_CountryIndustries.some((record) => { 19         return record.industry === knownfor; 20     }); 21 22     if (!isFound) { 23         eventData.eventProcessed = true; 24 25         this.ViewController.ErrorGroupPanel.clearErrorGrid(); 26         const errors: Error[] = []; 27 28         let message: string = "Known For value should be present in the Industries list"; 29         errors.push(new Error({message: message, fieldName: "KnownFor", severity : 1})); 30 31         this.ViewController.ErrorGroupPanel.addErrorsToErrorGrid(errors); 32         this.ViewController.ErrorGroupPanel.showErrorGrid(); 33     } 34 } 35 } 36 37 export class CountryFormHandler extends QraViewFormTSHandlerV2\<DTO.CountryMaint> { }

Check the "Active" checkbox.

Then click Compile, and, if successful, click Save button.

Save the Business Component!

15 | public onBeforeUpdate(eventData: EventData.QraView\.BeforeUpdateEventData, processEvent: (processIt?: boolean) => void): void { 16 |     const knownfor: string = this.NgData._com_extensions_training_CountryExtension[0].knownFor; 17 |     const isFound: boolean = this.NgData._com_extensions_training_CountryIndustries.some((record) => { 18 |         return record.industry === knownfor; 19 |     }); 20 | 21 |     if (!isFound) { 22 |         eventData.eventProcessed = true; 23 | 24 |         this.ViewController.ErrorGroupPanel.clearErrorGrid(); 25 |         const errors: Error[] = []; 26 | 27 |         let message: string = "Known For value should be present in the Industries list"; 28 |         errors.push(new Error({message: message, fieldName: "KnownFor", severity : 1})); 29 | 30 |         this.ViewController.ErrorGroupPanel.addErrorsToErrorGrid(errors); 31 |         this.ViewController.ErrorGroupPanel.showErrorGrid(); 32 |     } 33 | } 34 | 35 | export class CountryFormHandler extends QraViewFormTSHandlerV2\<DTO.CountryMaint> { }

Check the “Active” checkbox.

Save the Business Component!

Check the “Active” checkbox.

Save the Business Component!

engineering_drawing

<page_number>23</page_number>

# QAD Enterprise Platform

# Using of data from the extension

Screenshot of the QAD Enterprise Platform interface showing Country Industries and Country Extension sections with an error message.

Navigate to Countries screen.

Enter into KnownFor field any value (e.g Cars) which are not present in Industries.

Click save and pay attention that Error is appear.

24

QAD Enterprise Platform

# What Happens Here?

**onBeforeUpdate** event

Standard event which happens each time before sending of data to the server for Create or Update. Could be aborted by `eventData.eventProcessed = true` if UI calidation raised an error.

**this.NgData._com_extensions_training_ContryExtension**

Way to get data not from the parent record for this page, but from the child extension.

**this.ViewController.ErrorGroupPanel** object

Object which allow to control ErrorPanel grid. Contains such methods as `clearErrorGrid`, `hideErrorGrid()`, `showErrorGrid()`, `addErrorsToErrorGrid()`, etc.

**new Error({message: message, fieldName: "KnownFor", severity : 1})**

Way to create standard Qad error for ErrorGrid. Pay attention that it’s not a JS Error constructor, so it should be imported from `Qad.Common.DTO.Error`.

<page_number>

25
</page_number>

# Using of Grids

Logo

logo

<page_number>26</page_number>

# QAD Enterprise Platform

# Using of Grids

UI screenshot of a QAD grid interface

<u>Students grid should display a</u> <u>flash warning message if after click</u> <u>on the New button, the Capacity of</u> <u>the training is exceeded.</u>

logo

Main TrainingRoom Students Start Date 10/25/2023 1:19 AM Capacity 5 Confirm Duration Days 3 Student Count Average Score 44.40 Students +New Delete More First Name Last Name : Score Moe Howard 55 Joe Kent 62 Lou Malnotti 25 Arthur Treacher 35 Bruce Wayne 45 < < > > 50 Records per Page

<page_number>27</page_number>

# QAD Enterprise Platform

# Using of Grids

## Form

Screenshot of the QAD Enterprise Platform interface showing the Form section with an Event Handlers grid. The grid has columns for Timing, Active, Applies To, App, and App URI. A red arrow points from a text box on the right to the "Details" button in the grid toolbar.

Open Training Business Component.

Scroll to Form.

Click Details to open previously created Event handler.

QAD Logo

<page_number>28</page_number>

# QAD Enterprise Platform

## Using of Grids

### Event Handlers

**Training**      **training**\
Business Component App

**Main**

**Main**
**Active** [x]
**Timing** Primary      Primary event handler for this business component
**Applies To** Web\
**App** training      urn:app:com.extensions.training

```typescript
1  module com.extensions.training.EventHandler.Training.ComExtensionsTraining.Maint_PRIMARY {
2      "use strict";
3
4      import QraViewTSHandlerWithViewFormTSHandler = Qad.QraView.TSHandler.QraViewTSHandlerWithViewFor
5      import QraViewFormTSHandlerV2 = Qad.QraView.TSHandler.QraViewFormTSHandlerV2;
6      import ViewGridTSHandlerV2 = Qad.QraView.TSHandler.ViewGridTSHandlerV2;
7      import IViewField = Qad.QraView.TSHandler.IViewField;
8      import DTo = com.extensions.training.EventHandler.Training.DTo;
9      import Constants = com.extensions.training.EventHandler.Training.Constants;
10
11     export class TrainingMaintHandler extends QraViewTSHandlerWithViewFormTSHandler<DTo.TrainingMai
12         protected createViewFormTSHandler(): TrainingFormHandler {
```

* Download StudentsTSHandler.ts from materials for this class.

* Copy all code from TS file.

* Paste it instead of code in the editor.

* Click Compile, and, if successful, click Save button.

screenshot_from_computer

<page_number>29</page_number>

# QAD Enterprise Platform

## Using of Grids

Screenshot of QAD Enterprise Platform showing a Training screen with a Students grid. A warning message "Capacity of this training is exceeded" is displayed at the top. The screen shows fields for Start Date, Duration Days, Capacity (set to 5), Student Count (5), and Average Score (91.40). The Students grid contains records for Moe Howard and Joe Kent.

Navigate to Training screen.

Set Capacity to 5.

Add 5 records into the grid and, when you add one more record, expected warning will be displayed.

30

# QAD Enterprise Platform

# What Happens Here?

**onViewGridCreated** event

Standard event which executed when page is opened. It allow to attach handler for grids.

**onAutoGridNewButtonClick** event

Standard grid event which happens each time when user click new button in the grid.

**this.registerDestroyableObject(...)**

Standard method which allow to register QAD objects which should be automatically deleted from the memory when page is closed.

**StudentsOneToManyAutoGridHandler** class

Custom grid handler which based on ViewGridTSHandlerV2 and allow to override or extend grid behavior. (Pay attention that ViewGridTSHandlerV2 should be imported from Qad.QraView\.TSHandler.ViewGridTSHandlerV2).

<page_number>31</page_number>

QAD logo

QAD Inc.

<page_number>32</page_number>