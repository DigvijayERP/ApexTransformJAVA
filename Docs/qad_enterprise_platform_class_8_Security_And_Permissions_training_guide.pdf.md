QAD logo

# QAD

## Class 8: QAD Enterprise Platform - Security and Permissions

By Don Springer

logo

QAD Enterprise Platform

# Topics

* QAD Security Model
* Users, Roles and Permissions
* Role Menus
* Configuration Data Import/Export
* Field Groups
* Record Level Security
* Security Control

QAD logo

logo

2

# QAD Security Model

QAD logo

logo

<page_number>3</page_number>

# Security and Permissions

# Authorization

How authenticated user is granted access to a resource:

### How authenticated user is granted access to a resource

| Step       | Relationship | Target     |
| ---------- | ------------ | ---------- |
| User       | Assigned     | Role       |
| Role       | Assigned     | Permission |
| Permission | Access       | Resource   |


logo

<page_number>4</page_number>

# Security and Permissions

# User Access

Hierarchy tree structure which allow to configure user access on different levels:

red circle icon System

Red circle icon Domain

| System   |
| -------- |
| Domain   |
| Entities |
| Sites    |


Red circle icon Entities

red circle icon Sites

| Step   |
| ------ |
| System |
| Domain |
| Entity |
| Site   |


Entity

Site

System

Domain

logo

<page_number>5</page_number>

# User and Role

logo

Logo
<page_number>6</page_number>

# Security and Permissions

# Add A User

* Main
  * User ID: trainusr
  * User Name: Training User
  * User Type: Employee
  * Active: [x]
  * Email Address: <trainusr@qad.com>
  * Email Definition: [ ]
  * Email Login: [x]
  * Menu Substitution: [ ]
  * Remarks: [ ]
  * Variant: [ ]
  * Restricted: [ ]
  * Initials: [ ]

* Locale
  * Language: English (United States)
  * Format Locale: English (United States)
  * Country Code: us
  * Time Zone: EST/EDT
  * Access Location: HO

* Access
  * System Access
    * System Access Enabled: [x]
    * Enabled Reason: QAD_DEF
    * Last Logon: [ ]
    * Date Password Last Changed: [ ]

Select “Users” from the menu.

Click “New” and fill next fields:
User ID: trainusr
User Name: Training User
Email Address:

<trainusr@qad.com>

Check Email Login checkbox.

Then set next fields:
Country Code: us
Access Location: HO
Enabled Reason: QAD_DEF

Click Save.

QAD logo

logo

7

<mark>Security and Permissions</mark>

# Add a User

Screenshot of the Set Password dialog box in the QAD Enterprise Application interface. The dialog shows fields for Password and Confirm Password with validation rules: at least 0 characters, at least 0 letter(s), at least 0 number(s), and passwords must match. Below the dialog, a table shows a user entry with Description "Enterprise Application", Active status checked, and Date "10/17/2023".

You will be prompted to set a password.

Enter the password: qad

Also, enter the same Confirm Password.

Click Set Password.

QAD logo

<page_number>8</page_number>

# **Security and Permissions**

**Create a Role**

| Role Name         | Role     | Role Label | App                |
| ----------------- | -------- | ---------- | ------------------ |
| AccountingClerk   | Training | Training   | Configuration Data |
| AccountingManager |          |            |                    |
| APClerk           |          |            |                    |
| APSupervisor      |          |            |                    |
| ARClerk           |          |            |                    |
| ARSupervisor      |          |            |                    |
| BusinessDevelRep  |          |            |                    |


Open “Roles” from the menu and click “New”.

Enter Training as Role and Role Label.

Be Sure that Active checkbox is checked.

Click Save.

logo

<page_number>9</page_number>

# User Access

Company logo

logo

<page_number>10</page_number>

**Security and Permissions**

# Assign Role to User

Screenshot of User Access screen showing search results for User ID starting with "train"

From the menu choose "User Access".

Enter train into the search field and click Search.

Double click on trainusr record.

QAD logo

<page_number>11</page_number>

# **Security and Permissions**

# Assign Role to User

| Role Description    | Role Name         | Active |
| ------------------- | ----------------- | ------ |
| Accounting Clerk    | AccountingClerk   | \[x]   |
| Accounting Mana...  | AccountingMana... | \[x]   |
| AP Clerk            | APClerk           | \[x]   |
| AP Supervisor       | APSupervisor      | \[x]   |
| AR Clerk            | ARClerk           | \[x]   |
| AR Supervisor       | ARSupervisor      | \[x]   |
| Business Develop... | BusinessDevelRep  | \[x]   |
| Buyer               | Buyer             | \[x]   |


Select System in the Domain tree.

Check Access checkbox.

Pay attention that it will become all Domains selected.

logo

<page_number>12</page_number>

Security and Permissions

# Assign Role to User

Screenshot of the Assign Role to User interface showing a hierarchical tree on the left and role details on the right.

**Main**

* System (0 Roles)

  * Domain: 10USA (0 Roles)

    * Entity: 10CORRCONS (0 Roles)

    * Entity: 10USACO (0 Roles)

  * Domain: 11CAN (0 Roles)

    * Entity: 11CANCO (0 Roles)

    * Entity: 11NACONS (0 Roles)

  * Domain: 12MEX (0 Roles)

    * Entity: 12MEXCO (0 Roles)

Click on Domain 10USA and check the Default Domain checkbox.

Then click Save.

QAD logo

screenshot_from_computer

<page_number>13</page_number>

**Security and Permissions**

# Assign Role to User

Screenshot of the QAD user interface showing the assignment of roles to a user within a specific domain. The left panel shows a hierarchy of domains and entities. The center panel lists roles for the selected domain "10USA | USA Division", with "Training" and "Member can run the WebUI" checked. Red arrows point from the explanatory text on the right to these checked boxes.

Select and check the Training role from the list of roles. This action will assign selected role to the user.

We also need to check “Member can run the WebUI” to allow the trainusr user use the Adaptive UX.

screenshot_from_computer

<page_number>14</page_number>

# **Security and Permissions**

# Assign Role to User – Site Level

| User ID  | User Name         | Main                         |
| -------- | ----------------- | ---------------------------- |
| Train    | Employee Training | System (2 Roles)             |
| trainusr | trainusr          | Domain: 10USA (2 Roles)      |
|          |                   | Entity: 10CORPCONS (2 Roles) |
|          |                   | Entity: 10USACO (2 Roles)    |
|          |                   | Site: 10-100 (2 Roles)       |
|          |                   | Site: 10-200 (2 Roles)       |
|          |                   | Site: 10-201 (2 Roles)       |
|          |                   | Site: 10-202 (2 Roles)       |
|          |                   | Site: 10-220 (2 Roles)       |
|          |                   | Site: 10-221 (2 Roles)       |
|          |                   | Site: 10-300 (2 Roles)       |
|          |                   | Site: 10-301 (2 Roles)       |
|          |                   | Site: 10-302 (2 Roles)       |
|          |                   | Site: 10-303 (2 Roles)       |
|          |                   | Site: 10-400 (2 Roles)       |
|          |                   | Site: 10-500 (2 Roles)       |
|          |                   | Site: 10-600 (2 Roles)       |
|          |                   | Site: 10-900 (2 Roles)       |


Usually, it will be enough to configure domain level access, but Enterprise Platform also supports the Site level configuration.

It could be useful in some specific cases, such as functionality from the EAM app.

logo

icon

<page_number>15</page_number>

# Role Menu

Logo

logo

<page_number>16</page_number>

Security and Permissions

# Add a Role Menu

Screenshot of the Menus screen in QAD Enterprise Platform showing the creation of a new Role menu named "Training". The interface shows a list of existing roles like AccountingClerk and APClerk on the left, and a configuration pane on the right where "Type" is set to "Role" and "Name" is set to "Training".

Open “Menus” screen from the menu and click New.

Select Type: Role and enter Training as the Name.

Then click ‘Add Page’.

<page_number>17</page_number>

# **Security and Permissions**

**Add a Role Menu**

### New Menu Item

| Search Query  | Training |
| ------------- | -------- |
| Results Count | 4        |
| Result Item   | Training |


x symbol

New Menu Item

search icon Training|

Close icon

4 Results

The New Menu Item panel will appear.

Let’s add the “Training” business component.

Type Training in the Search box and choose the “Training” from the results.

<page_number>18</page_number>

**Security and Permissions**

# Add a Role Menu

Screenshot of the "Add Page" dialog box within the "New Menu Item" interface, showing the "Name" field as "Training" and a "Folder" dropdown menu.

Keep in mind that for larger Role Menus, you can add folders to organize the options you add.

Click Done.

<page_number>19</page_number>

# **Security and Permissions**

# Add a Role Menu

**Main**

| Type | Role     |
| ---- | -------- |
| Name | Training |


**Menu**

Add Page | Add Folder | Rename Folder

View | All |

Training

**Properties**

| Resource URI               | urn:view:hybridbrowse:com.extensions.training.traini... |
| -------------------------- | ------------------------------------------------------- |
| Include in Mobile App Menu | ✅                                                       |


You can see the Training business component on the Menu which we are created.

Logo

engineering_drawing

logo

icon

20

Security and Permissions

# Add a Role Menu

Let’s add another option.

Screenshot of the QAD Enterprise Platform interface showing the "New Menu Item" dialog box with "training room" typed into the search field and "Training Room" selected from the results.

Click Add Page.

Type Training Room in the Search box and choose appropriate option from the results.

Click “Done”.

Then click Done for the Add Page Dialog box.

Then click Save for the Role Menu.

QAD logo

<page_number>21</page_number>

Security and Permissions

# Add a Role Menu

Screenshot of the Add a Role Menu interface showing the Main and Menu sections with a red arrow pointing to the Permissions button.

Now as you can see, our Role Menu has two options.

The permissions button at the bottom of the Role Menu page brings you to the Role Permissions screen, where resources will be filtered according to the options added into the current menu.

Click on it.

22

22

Security and Permissions

# Add a Role Menu

Screenshot of the QAD Enterprise Platform interface showing the Role Permissions screen for a role named "Training". The screen is divided into a navigation tree on the left and a permissions grid on the right. The navigation tree shows "Training" and "Training Room" nodes, each with a sub-node for "APIs". The permissions grid for "Training" shows "Full Access", "Create", "Delete", "Read", and "Write" permissions, all with the "Allow" checkbox checked. A red arrow points from a text box at the bottom labeled "Add permissions for both components" to the "Training" node in the tree and the "Allow" header in the permissions grid.

Add permissions for both components

23

Security and Permissions

# Role Permissions for Training role

## Training Permissions

| Permission  | Allow  |
| ----------- | ------ |
| Full Access | \[yes] |
| Create      | \[yes] |
| Delete      | \[yes] |
| Read        | \[yes] |
| Write       | \[yes] |


**URI**: urn:be:com.extensions.training.Training.ITraining

**Menu Eligible**: [ ]

For comparison purposes open Role Permissions directly from the main menu and chose the Training Role

screenshot_from_computer

<page_number>24</page_number>

# **Security and Permissions**

# Add a Role Menu

QAD Training interface screenshot

Let’s Login as:

<trainusr@qad.com>

.

Update the password if required during the login process.

Find the Training role menu on the top.

See that it contains two options which we added:
Training and Training Room

Please note that Role Menus are Web UI ONLY!

In the NetUI standard menu options are filtered by your access rights.

Action icon

logo

icon

RQAD Training W Training Training Room 4 Training <No Stored View> + New Edit More Class Name starts with Search Class Name : Location Start Date Duration Days : Student Count Stamping Machine ... Detroit 15 1 Sales Order Santa Barbara 10/12/2023 1:19 ... 5 5 Purchasing Chicago 10/10/2023 3:33... 10 9 Laser Cutter Mainte... Chicago 10/10/2023 12:00... 4 1

<page_number>25</page_number>

# Export & Import Configuration Data

logo

<page_number>26</page_number>

# **Security and Permissions**

# Export & Import Configuration Data

| Type     | Artifact              | Label                  | Business Component. | View | Status | D |
| -------- | --------------------- | ---------------------- | ------------------- | ---- | ------ | - |
| Artifact | Role, Menu & Permi... | Shop Floor Admin       |                     |      | Active |   |
|          |                       | Shop Floor Operator    |                     |      |        |   |
|          |                       | Shop Floor Quality     |                     |      |        |   |
|          |                       | Shop Floor Supervis... |                     |      |        |   |
|          |                       | Shop Floor Maint Te... |                     |      |        |   |
|          |                       | Training               |                     |      |        |   |
|          |                       | Training2              |                     |      |        |   |


Login using 

<mfg@qad.com>

.

Open the Configuration Data page from the main menu. Then type Role and click search.

Now look for the Artifact with Label “Training” and select it. It will appear selected as shown here.

logo

<page_number>27</page_number>

# **Security and Permissions**

# Export & Import Configuration Data

Configuration Data table with Actions menu open

| Type     | Artifact              | Label                  | View | Status |
| -------- | --------------------- | ---------------------- | ---- | ------ |
| Artifact | Role, Menu & Permi... | Shop Floor Admin       |      | Active |
|          |                       | Shop Floor Operator    |      |        |
|          |                       | Shop Floor Quality     |      |        |
|          |                       | Shop Floor Supervis... |      |        |
|          |                       | Shop Floor Maint Te... |      |        |
|          |                       | Training               |      |        |
|          |                       | Training2              |      |        |


Now click on Actions and choose “Export Configuration Data”.

logo

Configuration Data Factory View Open Actions More Individual Artifact starts with "role" Import Configuration Data Search Type 8 Artifact O Label : Bulk View O Status O Artifact Role, Menu & Permi... Shop Floor Admin Export Configuration Data Active Artifact Role, Menu & Permi... Shop Floor Operator Active Artifact Role, Menu & Permi... Shop Floor Quality Active Artifact Role, Menu & Permi... Shop Floor Supervis.. Active Artifact Role, Menu & Permi... Shop Floor Maint Te... Active Artifact Role, Menu & Permi... Training Active Artifact Role, Menu & Permi... Training2 Active

28

Security and Permissions

# Export & Import Configuration Data

Screenshot of the Export Configuration Data screen in QAD Enterprise Platform, showing the Export Artifacts tab with the "Training" artifact selected.

Choose only the Training Artifact checkbox. Then click the Submit Button.

screenshot_from_computer

<page_number>29</page_number>

Security and Permissions

# Export & Import Configuration Data

Screenshot of the QAD Enterprise Platform interface showing the Inbox with a notification for "Export Configuration Data". A callout box instructs the user to open the notification and click Download. Below, the "Recent Downloads" section shows the exported zip file.

Open your inbox and open the notification for "Export of Configuration Data"

Click Download.

screenshot_from_computer

icon

<page_number>

30
</page_number>

# **Security and Permissions**

# Export & Import Configuration Data

### Menus

| Name     |
| -------- |
| Training |


Now let's go to Menus and select the Training menu.

Then click Delete to remove it.

screenshot_from_computer

logo

<page_number>31</page_number>

Security and Permissions

# Export & Import Configuration Data

Screenshot of the Roles management interface in QAD Enterprise Platform, showing a "Training" role selected and the "Delete" button highlighted with a red arrow.

Open Roles and click Delete for the Training record.

QAD logo

<page_number>

32
</page_number>

Security and Permissions

# Export & Import Configuration Data

Screenshot of the QAD Enterprise Platform interface showing a Role configuration screen for "Training" with an error message at the bottom.

You will get an error message saying you cannot delete the role while it is assigned to members.

| Field | Error                                                       |
| ----- | ----------------------------------------------------------- |
| Role  | Role has one or more members and cannot be deleted Training |


screenshot_from_computer

<page_number>

33
</page_number>

Security and Permissions

# Export & Import Configuration Data

Screenshot of the Roles interface showing the "Remove All Role Members" action and confirmation dialog.

Use the "Remove All Role Members" option.

This will unassign all the members of the role.

Click Continue at the confirmation message.

QAD logo

screenshot_from_computer

screenshot_from_computer

screenshot_from_computer

<page_number>

34
</page_number>

Security and Permissions

# Export & Import Configuration Data

Screenshot of the Roles management interface in QAD Enterprise Platform, showing a "Training" role selected and a red arrow pointing from a text box at the bottom to the "Delete" button in the top toolbar.

Try to delete Training role one more time.

QAD logo

<page_number>35</page_number>

Security and Permissions

# Export & Import Configuration Data

Screenshot of the Import Configuration Data screen in QAD Enterprise Platform, showing the "Choose file" button and a file explorer window selecting "Export_Config_Data_2023_10_18.zip" from the Downloads folder.

Next open Configuration Data screen, choose Import action, and then select the File we just exported.

QAD logo

screenshot_from_computer

<page_number>

36
</page_number>

Security and Permissions

# Export & Import Configuration Data

Configuration Data > Import Configuration Data

Screenshot of the Import Configuration Data interface showing the Import Artifacts tab with a list of items to be imported, including Role, Menu & Permissions. An arrow points from the list to the Submit button.

Review the content of file in the preview, and then click Submit.

QAD logo

screenshot_from_computer

<page_number>

37
</page_number>

Security and Permissions

# Export & Import Configuration Data

Screenshot of the QAD Enterprise Platform interface showing the Menus configuration screen and an Inbox notification confirming a successful configuration data import.

Open the Inbox to see the confirmation that the import was successful.

Verify that the Training role and appropriate Role Menu are returned.

screenshot_from_computer

screenshot_from_computer

<page_number>

38
</page_number>

# **Security and Permissions**

# Export & Import Configuration Data

User Access interface

Go to User Access and find Training User.

Assign the Training Role back and click Save.

|   | Role Description         | Role Name           | Active |
| - | ------------------------ | ------------------- | ------ |
| ☐ | Tax Manager              | TaxManager          | ☑      |
| ☐ | Technical Support Rep    | TechnicalSupportRep | ☑      |
| ☑ | Training                 | Training            | ☑      |
| ☐ | Training2                | Training2           | ☑      |
| ☐ | Treasury Manager         | TreasuryManager     | ☑      |
| ☐ | User Interface Design    | uidesign            | ☑      |
| ☐ | Value Stream Analyst     | ValueStreamAnalyst  | ☑      |
| ☐ | VP Logistics             | VPLogistics         | ☑      |
| ☐ | VP Marketing             | VPMarketing         | ☑      |
| ☐ | VP Sales                 | VPSales             | ☑      |
| ☐ | VP Services              | VPServices          | ☑      |
| ☐ | VP Supply Chain          | VPSupplyChain       | ☑      |
| ☑ | Member can run the WebUI | webui\_user         | ☑      |


Action icon

icon

User Access <No Stored View>More trainusr trainusr Yes User ID User Name User Name User ID Active Train Employee Training Main trainusr trainusr Main System (1 Roles) System Access Roles (1) Role Description Role Name Active 0 Tax Manager TaxManager 0 0 Technical Support Rep TechnicalSupportRep 0 Training Training 0 Training2 Training2 0 0 Treasury Manager TreasuryManager a 0 User Interface Design uidesign 0 0 Value Stream Analyst ValueStreamAnalyst 3 0 VP Logistics VPLogistics U 0 VP Marketing VPMarketing 0 0 VP Sales VPSales S 0 VP Services VPServices 0 0 VP Supply Chain VPSupplyChain 0 V Member can run the WebUl webui_user 3 < < > > 2 Save Cancel

39

# **Field Groups**

logo

Logo 40
<page_number>40</page_number>

# Security and Permissions

**Field Groups**

| Main          | Main | Main          | Main |
| ------------- | ---- | ------------- | ---- |
| Class Name    |      | Topic Type    |      |
| Location      |      | Area of Study |      |
| Country       |      | Class Value   |      |
| Start Date    |      | Capacity      |      |
| Duration Days |      | Student Count | 0    |
|               |      | Average Score | 0.00 |
| ***           |      |               |      |
| Main          |      |               |      |
| Class Name    |      | Topic Type    |      |
| Location      |      | Area of Study |      |
| Country       |      | Class Value   |      |
| Start Date    |      | Capacity      |      |
|               |      | Student Count | 0    |
|               |      | Average Score | 0.00 |


Field Groups allow you to use Field Level Security.

As an example, you can allow SuperUser role to have full access for the Training fields and configure Training role to have only read access for Start Date and disallow access for Duration fields.

logo

engineering_drawing

screenshot_from_computer

<page_number>41</page_number>

# Security and Permissions

**Field Groups**

You can create different field groups for different sets of fields according to their business logic.

⌄ Field Groups

| Field Group Code | Field Group Label |
| ---------------- | ----------------- |
| Main             |                   |
| Options          |                   |


Field Groups will allow you to set permissions for the whole group or for each field separately

| Permission  | Allow |
| ----------- | ----- |
| Full Access | ☑     |
| Create      | ☑     |
| Delete      | ☑     |
| Read        | ☑     |
| Write       | ☑     |


### Field Groups Structure

| Category      |
| ------------- |
| Field Groups  |
| Main          |
| Options       |
| Duration Days |
| Start Date    |


logo

screenshot_from_computer

screenshot_from_computer

screenshot_from_computer

<page_number>42</page_number>

# Record Level Security

logo

Logo
43

# Security and Permissions

## Record Level Security

Screenshot of a QAD Enterprise Platform browse showing records for Training with columns Class Name, Location, Description, and Start Date.

In some cases, it could be useful to configure access to records of business components.

Business component browses support Record Level Security mechanism which allows to obtain this.

QAD logo

<page_number>44</page_number>

**Security and Permissions**

# Record Level Security

Screenshot of Record Level Security configuration screen in QAD Enterprise Platform

By default, after activation of Record Level Security, a configuration ‘Owner’ will be applied.

It means that user will only see that records which were created by itself.

Please pay attention, that it’s impossible to turn-on Record Level Security for legacy .Net browses.

QAD logo

45

# Security and Permissions

# Record Level Security

| User ID ↕ |   | User Name ▲ |
| --------- | - | ----------- |
| trainusr  |   |             |


With Record Level Security you also can provide a conditional access to records for some Security Group.

Of course, initially a Security Group should be defined, and you should define which users will be included there.

logo

<page_number>46</page_number>

# Security and Permissions

# Record Level Security

Security Rules interface

Then you will be able to define Security Rules which include access criteria in which record should be available and Security Group or User for which that record is available if criteria was met.

logo

Security Rules <No Stored View> + New More TrainGroup_Trainin_Access Training Rule : Rule Label Rule Label Business Component Label Main Criteria Applies To Main Rule CodeTrainGroup_Trainin_Access Active Rule Label TrainGroup_Trainin_Access α Scope Business Component urn:be:com.extensions.training.Training.ITraini.. O Training Description Criteria +New Delete Preview Field : Operator : Value 1 : Value 2 : Training.Class Name contains Sales < >> 50 Records per Page 1-1of1 Applies To +New Delete Type : Name Applies To Parents Permissions : Group TrainGroup a No Full Access << 4 > > 2 Save Cancel

<page_number>47</page_number>

Security and Permissions

# Record Level Security

Screenshot of a software interface showing a filtered list of training records. The breadcrumb path is Security Rules > Training. The table shows one record: Class Name "Sales Order", Location "Santa Barbara", Description "UNITED STATES", Start Date "10/12/2023 1:19 PM", Duration Days "5", Student Count "5", and Average Score "44.40".

An example of Record Level Security configuration:
User can see only that records which contain ‘Sales’ in Class Name.

QAD logo

<page_number>48</page_number>

# **Security Control**

logo

Logo
<page_number>49</page_number>

# Security and Permissions

**Security Control**

Security Control

| Main                    | Main                             | Main                        | Main               |
| ----------------------- | -------------------------------- | --------------------------- | ------------------ |
| Idle Timeout Minutes    | 60                               | Maximum Access Failures     | 10                 |
| Session Expires Minutes | 1440                             | Email System                | 500                |
| Header Display Mode     | 0 Display Date                   | Logon History Level         | Failed Only Failed |
| Administrator Role      | SuperUser                        | Enabled Reason Type         | USER\_ACT          |
| Auto-Disablement Reason | ForceOff Security Violation      | Enforce Licensed User Count |                    |
| Client ID               | d2f9045d6bed47be2e14d22540cada31 | Enforce OS User ID          |                    |


| Password                   | Password | Password                 | Password                       |
| -------------------------- | -------- | ------------------------ | ------------------------------ |
| Minimum Length             | 0        | Password Creation Method | No - Manually Created by Admin |
| Min Numeric Characters     | 0        | Password Expiration Days | 0                              |
| Min Non-Numeric Characters | 0        | Warning Days             | 0                              |
| Minimum Reuse Days         | 0        |                          |                                |
| Minimum Reuse Changes      | 0        |                          |                                |


Security Control is another aspect of security that is common for both Web UI and NetUI.

Here the complexity of password, sessions timeouts or main administrator role could be defined or modified.

logo

<page_number>50</page_number>

QAD Inc. logo
QAD Inc.

<page_number>51</page_number>