QAD logo

# QAD

## Class 6: QAD Enterprise Platform -

## Java Extensions

By Don Springer

logo

QAD Enterprise Platform

# Topics

* Java Extension Overview

* Initial Configuration

* Extension Example

QAD logo

<page_number>2</page_number>

# Java Extension Overview

Logo 3

logo

<page_number>3</page_number>

**QAD Enterprise Platform**

# What is Java Extension Framework?

The Java Extension Framework is the mechanism that allows a developer to inject custom logic into the lifecycle of Business Components.

**Java Extensions**

* allow modify or completely override the default behavior of a specific BC
* supported by platform and coded BCs
* are separated from the core QAD application and, as a result, are upgrade-safe

QAD logo

logo

**QAD Enterprise Platform**

# Java Extension workflow

Java Extension is a Maven-based Java project that contains custom code. When deployed, this extension injects custom logic into the standard application flow, executing it when specific Business Component methods are called.

### QAD Enterprise Platform: Java Extension workflow

| Step    | Action/Decision                                                            |
| ------- | -------------------------------------------------------------------------- |
| 1       | User saves record on BC screen on Web UI                                   |
| 2       | Web UI sends request to save record to Progress BL                         |
| 3       | Java Extension for this BC exists?                                         |
| 4 (No)  | Progress BL proceeds with create method on BC to save data to the Database |
| 4 (Yes) | Progress BL triggers execution of overridden "create" method in JEF        |
| 5 (Yes) | Overridden "create" method with custom code in JEF is executed             |
| 6 (Yes) | Extension code calls Progress BL back with super.create() method call      |
| 5       | Progress BL returns data to Web UI                                         |
| 6       | Web UI displays saved data to user                                         |


**QAD Enterprise Platform**

# How to Develop a Java Extension?

Java Extensions are developed in an IDE (Visual Studio Code) using a specialized plugin. This plugin provides all the necessary tools for the development lifecycle, including:

* setting up the correct project structure.
* managing dependencies.
* deploying the extension to a QAD environment.
* undeploying an extension.

QAD logo

logo

2 6

**QAD Enterprise Platform**

# Java Extension Capabilities

The Java Extension Framework provides a rich set of features for implementing custom logic. Key capabilities include:

* reading, creating, and modifying data in the target Business Component.
* creating extensions for both coded and platform Business Components.
* creating multiple extensions for the same Business Component.
* calling other Business Components to orchestrate complex processes.

QAD logo

logo

2 7

**QAD Enterprise Platform**

# Java Extension APIs

In addition to overriding Business Component methods, the framework provides a library of helper classes, known as the Java Extension APIs. These APIs simplify interaction with the core QAD application and services.

**Some of the provided APIs allow you to:**

* execute SQL Queries: securely fetch data directly from the database.
* access Session Context: get the current user ID, role, and domain.
* get translations: retrieve localized labels and messages.
* log Messages: write custom messages to the extension log file.
* make HTTP Calls: interact with external web services and APIs.

QAD logo

logo

2 8

# Initial Configuration

logo

Logo
<page_number>9</page_number>

**QAD Enterprise Platform**

# Installing Java 17

Open <u>

https://www.openlogic.com/openjdk-downloads

Choose:

Version 17, for Windows, Architecture x64, Package JDK.

Click the MSI download.

**OpenLogic's OpenJDK Downloads**

### Java Download Configuration

| Java Version | Operating System | Architecture | Java Package |
| ------------ | ---------------- | ------------ | ------------ |
| 17           | Windows          | x86 64-bit   | JDK          |


| JAVA VERSION | OPERATING SYSTEM | ARCHITECTURE | JAVA PACKAGE | DOWNLOAD |
| ------------ | ---------------- | ------------ | ------------ | -------- |
| 17.0.18+8    | Windows          | x86 64-bit   | JDK          | .msi     |
|              |                  |              |              | .zip     |


icon

icon

icon

icon

logo

# QAD Enterprise Platform

## Installing Java 17

Select the installation options as shown and install JDK.

OpenLogic by Perforce logo
**Welcome to the OpenLogic-OpenJDK JDK with Hotspot 8u432-b06 (x64) Setup Wizard**

The Setup Wizard will install OpenLogic-OpenJDK JDK with Hotspot 8u432-b06 (x64) on your computer. Click Next to continue or Cancel to exit the Setup Wizard.

Screenshot of OpenLogic-OpenJDK Setup Custom Setup window showing installation features like Add to PATH, Associate .jar, Set JAVA_HOME variable, and JavaSoft (Oracle) registry.

QAD logo

11

screenshot_from_computer

# QAD Enterprise Platform

## Installing Maven

Apache Maven Project logo

* Navigate to https://maven.apache.org/
* Click on the Link "Download, Install, Configure, Run"
* Download Latest Binary Zip file.

Apache / Maven / Welcome to Apache Maven edit icon

### Welcome to Apache Maven

Apache Maven is a software project management and comprehension tool. Based on the concept of a project object model (POM), Maven can manage a project's build, reporting and documentation from a central piece of information.

If you think that Maven could help your project, you can find out more information in the "About Maven" section of the left hand navigation. This includes an in-depth description of what Maven is and a list of some of its main features.

This site is separated into the following sections, depending on how you'd like to use Maven:

| Use | Download, Install, Configure, Run Maven                          |
| --- | ---------------------------------------------------------------- |
|     | Information for those needing to build a project that uses Maven |


**Left Navigation Menu:**

* Welcome
* License
* ABOUT MAVEN
* What is Maven?
* Features
* Download
* Use
* Release Notes

QAD logo

12

# QAD Enterprise Platform

# Installing Maven

Screenshot of Maven extraction process showing destination folder selection

Maven does not require installation. Just extract the archive to a directory of your choice.

E.g:
C:\Program Files\Maven\apache-maven-x.x.x

where x.x.x the actual version of downloaded package.

QAD logo

13

# QAD Enterprise Platform

## Installing Maven

To add Maven to the PATH:

1. From File Explorer make right click on This PC and choose properties
2. Then choose Advanced System Settings

Screenshot of File Explorer showing This PC

Screenshot of Windows System About settings page highlighting Advanced system settings

QAD logo

icon

<page_number>14</page_number>

QAD Enterprise Platform

# Installing Maven

3. In the Advanced tab Click Environment Variables

Screenshot of Windows System Properties dialog box showing the Advanced tab and the Environment Variables button.

QAD logo

<page_number>15</page_number>

# QAD Enterprise Platform

# Installing Maven

File explorer and system variable windows

Verify that JAVA_HOME environment variable is present and refer to JDK which you just installed.

| Variable               | Value                                              |
| ---------------------- | -------------------------------------------------- |
| FP\_NO\_HOST\_CHECK    | NO                                                 |
| JAVA\_HOME             | C:\Program Files\OpenLogic\jdk-8.0.432.06-hotspot\ |
| MAVEN\_HOME            | C:\Program Files\Maven\apache-maven-3.6.3          |
| NUMBER\_OF\_PROCESSORS | 3                                                  |
| OS                     | Windows NT                                         |


logo

File Home Share View ← ↑ >This PC > OS (C:)> Program Files > OpenLogic Documents Name ^ < Date modified Type Drivers jdk-8.0.412.08-hotspot 7/25/2024 1:05 PM File folder ESD jdk-8.0.432.06-hotennt 12/1/2024.5:29.PM File folder Intel jdk-8.0.432.06-hotspot Properties × PerfLogs General Sharing Security Previous Versions Customize Program File 3T Software dk-8.0.432.06-hotspot Classic She Common F Type: File folder (.06-hotspot) Edit System Variable × Variable name: JAVA_HOME Variable value: C:\Program Files\OpenLogic\jdk-8.0.432.06-hotspot Browse Directory... Browse File... OK Cancel vivervdla Cnuuw(ysLem(meNvedtd FP_NO_HOST_CHECK NO 2 JAVA_HOME C:\Program Files\OpenLogic\jdk-8.0.432.06-hotspot\ MAVEN_HOME C:\ProgramFiles\Maven\apache-maven-3.6.3 NUMBER_OF_PROCESSORS 3 OS Windows NT New\... Edit... Delete

# QAD Enterprise Platform

# Installing Maven

File explorer and system variable windows

Create or Edit the MAVEN_HOME environment variable and set as Value the path of the extracted Maven.

| Variable               | Value                                              |
| ---------------------- | -------------------------------------------------- |
| DriverData             | C:\Windows\System32\Drivers\DriverData             |
| FP\_NO\_HOST\_CHECK    | NO                                                 |
| JAVA\_HOME             | C:\Program Files\OpenLogic\jdk-8.0.432.06-hotspot\ |
| MAVEN\_HOME            | C:\Program Files\Maven\apache-maven-3.6.3          |
| NUMBER\_OF\_PROCESSORS | 3                                                  |
| OS                     | Windows NT                                         |


logo

This PC > OS (C:) > Program Files > Maven ts^ Name ^ Date modified Type Size apache-maven-3.6.3 7/25/2024 1:30 PM File folder apache-maven-3.9, 10/7/7004.0.52.AM4 Cilfald apache-maven-3.9.9 Properties × General Sharing Securty Previous Versions Customize File 'are apache-maven-3.9.9 he Type: File folder (.9) n F Location: C:\Program Files\Maven Size: 10.1 MB (10,635,235 bytes) Size on disk: 10.2 MB (10,780.672 bytes) Edit System Variable × Variable name: MAVEN_HOME Variable value: C:\Program Files\Maven\apache-maven-3.6.3 Browse Directory... Browse File... OK Cancel 2¹ᵈ vivervald Ci(nuuwsoystemc(yhvers(nvervatd FP_NO_HOST_CHECK NO JAVA_HOME C:\Program Files\OpenLogic\jdk-8.0.432.06-hotspot\ MAVEN_HOME C:\Program Files(Maven\apache-maven-3.6.3 NUMBER_OF_PROCESSORS 3 oS Windows NT

**QAD Enterprise Platform**

# Installing Maven

Ensure that %MAVEN_HOME%\bin is present in the Path.

| Variable           | Value                                     |
| ------------------ | ----------------------------------------- |
| IntelliJ IDEA      | %USERPROFILE%\\.IntelliJIdea2019.3\system |
| JETBRAINS\_LICENSE | C:\Users\Public\JetBrains\Licenses        |
| OneDrive           | C:\Users\User\OneDrive                    |
| OneDriveCommercial | C:\Users\User\OneDrive - Company          |
| Path               | %MAVEN\_HOME%\bin;%JAVA\_HOME%\bin;...    |
| TEMP               | %USERPROFILE%\AppData\Local\Temp          |
| TMP                |                                           |


| Variable               |
| ---------------------- |
| ComSpec                |
| DriverData             |
| JAVA\_HOME             |
| MAVEN\_HOME            |
| NUMBER\_OF\_PROCESSORS |
| OS                     |
| Path                   |
| PATHEXT                |


| %USERPROFILE%\AppData\Local\Microsoft\WindowsApps            |
| ------------------------------------------------------------ |
| %IntelliJ IDEA%                                              |
| C:\Users\dpetin\AppData\Local\Programs\Microsoft VS Code\bin |
| %MAVEN\_HOME%\bin                                            |
|                                                              |
|                                                              |
|                                                              |
|                                                              |
|                                                              |
|                                                              |
|                                                              |
|                                                              |
|                                                              |
|                                                              |
|                                                              |
|                                                              |


logo

# QAD Enterprise Platform

## Installing Java and Maven

```
C:\Windows\System32>java -version
openjdk version "17.0.18" 2026-01-20
OpenJDK Runtime Environment OpenLogic-OpenJDK (build 17.0.18+8-adhoc..jdk17u)
OpenJDK 64-Bit Server VM OpenLogic-OpenJDK (build 17.0.18+8-adhoc..jdk17u, mixed mode, sharing)

C:\Windows\System32>mvn -version
Apache Maven 3.9.12 (848fbb4bf2d427b72bdb2471c22fced7ebd9a7a1)
Maven home: C:\Program Files\Maven\apache-maven-3.9.12
Java version: 17.0.18, vendor: OpenLogic, runtime: C:\Program Files\OpenLogic\jdk-17.0.18.8-hotspot
Default locale: en_US, platform encoding: Cp1251
OS name: "windows 11", version: "10.0", arch: "amd64", family: "windows"

C:\Windows\System32>
```

QAD logo

To verify that installation was successful, open Command Prompt. Run next commands:

java –version

mvn - version

19

**QAD Enterprise Platform**

# Visual Studio Code

Visual Studio Code logo Visual Studio Code Docs Updates Blog API Extensions FAQ GitHub Copilot 🌙

Version 1.95 is now available! Read about the new features and fixes from October.

# Code faster with AI

Visual Studio Code with GitHub Copilot supercharges your
code with AI-powered suggestions, right in your editor.

Download for Windows Try GitHub Copilot

QAD logo
Install Visual Studio Code in your desktop environment.
Download the installation file from <u>

https://code.visualstudio.com/

</u>
Choose the “Download For Windows” option.

icon

logo

Visual Studio Code with GitHub Copilot supercharges you code with Al-powered suggestions, right in your editor.

# QAD Enterprise Platform

# Visual Studio Code

VS Code Extension Pack for Java interface

1. Open the Visual Studio Code.

2. Open Extensions panel and search for Extension pack for Java.

3. Select the version by Microsoft and click Install.

This will add the extension to your VS Code IDE and make it compatible for Java development.

QAD logo

logo

Search 00 EXTENSIONS: MARKETPLACE EP Extension: Extension Pack for Java × > Extension pack for Java Y Extension Pack for Java v0.29.0 Extension Pack for Java Microsoft microsoft.com C29,795,197 0 Popular extensions for Java devel... Microsoft Popular extensions for Java development that provides Ja.. 8 AUTO Extension Pack for 239K Disable Uninstall Switch to Pre-Release Version Auto l JDK Auto-Configuration + Extensi.. 10 Pleiades Install DETAILS FEATURES CHANGELOG Spring Boot Extensi... 2.6M A collection of extensions for dev... Extension Pack (7) VMware Install Categories Extension Pack for... 10sk 5 IntelliCode Programming Some of the most popular and us... Al-assisted development Languages Microsoft Instailed Loiane Groner Install Linters Debuggers

# QAD Enterprise Platform

## Visual Studio Code

1. Download the plugin "Visual Studio Code plugin for Java Extensions".

Screenshot of Visual Studio Code settings menu showing the Extensions option

2. Extract the contents of the ZIP file you downloaded. Inside the extracted contents, locate and extract the data.zip file. After extracting it, find the:
   qad-java-sse-vscode-x.x.x.vsix
   (x.x.x is the release number)

3. In the Visual Studio Code, click the Gear icon, and then choose Extensions.

QAD logo

22

**QAD Enterprise Platform**

4. Click the ellipsis button (...) at the end of the Extensions menu and choose "Install from VSIX" option.

**Visual Studio Code**

### Extension Menu Options

| Menu Item                              |
| -------------------------------------- |
| Views                                  |
| Check for Extension Updates            |
| Disable Auto Update for All Extensions |
| Enable All Extensions                  |
| Disable All Installed Extensions       |
| Show Running Extensions                |
| Start Extension Bisect                 |
| Install from VSIX...                   |


5. Select the qad-java-sse-vscode-x.x.x.vsix file and click install.

You will see a message about the completed installation. After this you will be able to run commands from the Command Palette.

It is recommended to restart Visual Studio Code after the plugin installation.

logo

# Extension Example

logo

Logo
<page_number>24</page_number>

# QAD Enterprise Platform

# Extension Example

Let's implement two additional requirements for the Training business component.

Screenshot of the Training business component interface showing fields like Class Name, Location, Country, Start Date, Duration Days, Topic Type, Area of Study, Class Value, Capacity, Student Count, and Average Score.

**Requirement 1:**
For each new record StartDate should be equal to current date.

QAD logo

1

screenshot_from_computer

# QAD Enterprise Platform

# Extension Example

Now, let's add two additional requirements for the Training business component.

Screenshot of the Training business component interface showing fields like Class Name (Purchasing), Location (Chicago), Country (us), Start Date (5/11/2026), Duration Days (5), Topic Type (Development), Area of Study (Distribution), Class Value (5), Capacity (8), Student Count (9), and Average Score (45.44).

**Requirement 2:**
During the save, for each record, the Capacity field should be mandatory.

QAD logo

2

# QAD Enterprise Platform

## Extension Example

Screenshot of Visual Studio Code showing the Command Palette with "QAD Extension: Init app" selected

Open Command Palette (F1) and choose “QAD: Init app command”

QAD logo

27

QAD Enterprise Platform

# Extension Example

Screenshot of Visual Studio Code and QAD My Developer Settings showing where to find and enter the environment URL. The VS Code prompt shows a URL field: 

https://aldpqjavaext01.environments.qad.com/clouderp

. The QAD My Developer Settings screen highlights the 'VS Code Plugin Connection URL' field. A text box on the right says 'Put your environment’s URL. You can find it in the My Development Settings page.'

<page_number>

28
</page_number>

# QAD Enterprise Platform

## Extension Example

Screenshot of a code editor showing a Client ID being entered into a prompt field.

Screenshot of the QAD Enterprise Platform Client IDs management page showing Client ID, Client Secret, and Description fields.

Next step requires to enter Client ID.

You can find it on the appropriate page or ask about it your environment Administrator.

29

# QAD Enterprise Platform

## Extension Example

Screenshot of user email input field: 

<mfg@qad.com>

. Press 'Enter' to confirm your input or 'Escape' to cancel

Screenshot of password input field: Enter QAD password. Press 'Enter' to confirm your input or 'Escape' to cancel

Next two steps require to enter credentials of active webui user.

Please pay attention that user should have Developer role.

QAD logo

30

# QAD Enterprise Platform

## Extension Example

Screenshot of VS Code showing the QAD Extension app selection dropdown with "Training" highlighted.

If login was successful, you should see a list of apps in which you can add Java extension. Let's select Training.

QAD logo

screenshot_from_computer

<page_number>31</page_number>

# QAD Enterprise Platform

## Extension Example

After saving of selected app, you should achieve an empty project structure.

Screenshot of Visual Studio Code showing an empty project structure for urn_app_com.extensions.training with folders config, data, lib, src, target, and files .gitignore, pom.xml

<page_number>32</page_number>

# QAD Enterprise Platform

# Extension Example

VS Code interface showing QAD extension command palette

Open Command Palette and choose “QAD: Update app dependency” command.

QAD logo

logo

File Edit Selection View Go Run Terminal Help Update EXPLORER QAD Extension: Init app recently used UNTITLED (WORKSPACE) QAD Extension: Undeploy urn_app_com.extensions.training QAD Extension: Build and Deploy config QAD Extension: Update app dependency × data Accounts: Manage Accounts other commands lib Accounts: Manage Extension Account Preferences.. src Accounts: Manage Trusted Extensions For Account target Accounts: Manage Trusted MCp Servers For Account .gitignore Add Data Breakpoint at Address pom.xml Add Function Breakpoint Add XHR/fetch Breakpoint

# QAD Enterprise Platform

## Extension Example

Screenshot of Visual Studio Code showing a project explorer with a Maven build success message in the terminal.

Progress will be displayed below in the Terminal

34

QAD Enterprise Platform

# Extension Example

Screenshot of Java project structure in an IDE showing Maven dependencies for a server-side extension

Result of the command execution you can find in the list of app dependencies. It will include services for each BC from the current app.

QAD logo

35

MAVEN

**QAD Enterprise Platform**

# Extension Example

Expand src/main/java path and via the right button click add a new class file into the training folder.

Set Training.java as a name.

| Menu Item          | Shortcut            |
| ------------------ | ------------------- |
| New                |                     |
| Class...           |                     |
| Interface...       |                     |
| Enum...            |                     |
| Record...          |                     |
| Annotation...      |                     |
| Abstract Class...  |                     |
| Package...         |                     |
| File...            |                     |
| Reveal in Explorer | Shift+Alt+R         |
| Copy Path          | Shift+Alt+C         |
| Copy Relative Path | Ctrl+K Ctrl+Shift+C |
| Rename             | F2                  |
| Delete             | Del                 |


logo

# QAD Enterprise Platform

## Extension Example

Expected result is next.

This is not an extension yet, a few steps left.

Screenshot of Visual Studio Code showing a Java project structure and the Training.java file with a basic class definition.

37

# QAD Enterprise Platform

# Extension Example

VS Code interface showing project explorer and Java code

Copy code from the file, which provided in materials for current class.

Put that code into your Training.java file.

```java
6     import com.extensions.training.training.TrainingDataSet;
7     import com.extensions.training.training.TrainingRecord;
8     import com.qad.ipc.dto.BCExecutionError;
9     import com.qad.ipc.dto.InputOutput;
10
11    import java.time.LocalDateTime;
12
13    @Extension
14    public class Training extends TrainingBaseService {
15      public void initialize(Output<TrainingDataSet> dsTraining) throws BCExecutionError {
16                super.initialize(dsTraining);
17                dsTraining.getValue().getTtTraining()[0].setStartDate(LocalDateTime.now());
18      }
19
20      @Override
21      public void create(InputOutput<TrainingDataSet> dsTraining) throws BCExecutionError {
22                this.validateCapacity(dsTraining);
23                throwAddedValidationErrors();
24
25                super.create(dsTraining);
26      }
27
28      @Override
29      public void update(InputOutput<TrainingDataSet> dsTraining) throws BCExecutionError {
30                this.validateCapacity(dsTraining);
31                throwAddedValidationErrors();
32
33                super.update(dsTraining);
34      }
35
36      private void validateCapacity(InputOutput<TrainingDataSet> dsTraining) {
37                TrainingRecord training = dsTraining.getValue().getTtTraining()[0];
38                if (training.getCapacity() == null || training.getCapacity() == 0) {
39                this.addValidationError("Capacity is mandatory");
40      }
41      }
42    }
```

**QAD Enterprise Platform**

Via the Command Palette (F1) run next command:

# Extension Example

| Command                                           | Shortcut               |
| ------------------------------------------------- | ---------------------- |
| QAD Extension: Build and Deploy                   |                        |
| QAD Extension: Update app dependency              |                        |
| QAD Extension: Init app                           |                        |
| QAD Extension: Undeploy                           |                        |
| Accounts: Manage Accounts                         |                        |
| Accounts: Manage Extension Account Preferences... |                        |
| Accounts: Manage Trusted Extensions For Account   |                        |
| Accounts: Manage Trusted MCP Servers For Account  |                        |
| Add Cursor Above                                  | Ctrl + Alt + UpArrow   |
| Add Cursor Below                                  | Ctrl + Alt + DownArrow |
| Add Cursors to Bottom                             |                        |
| Add Cursors to Line Ends                          | Shift + Alt + I        |
| Add Cursors to Top                                |                        |
| Add Data Breakpoint at Address                    |                        |
| Add Function Breakpoint                           |                        |


QAD: Build and Deploy.

Deploy.

logo

# QAD Enterprise Platform

## Extension Example

```java
6    import com.extensions.training.training.TrainingDataSet;
7    import com.extensions.training.training.TrainingRecord;
8    import com.qad.ipc.dto.BCExecutionError;
9    import com.qad.ipc.dto.InputOutput;
10
11   import java.time.LocalDateTime;
12
13   @Extension
14   public class Training extends TrainingBaseService {
15       public void initialize(Output<TrainingDataSet> dsTraining) throws BCExecutionError {
16           super.initialize(dsTraining);
17           dsTraining.getValue().getTtTraining()[0].setStartDate(LocalDateTime.now());
18       }
19   }
```

| \* Terminal will be reused by tasks, press any key to close it.                                                                                 |                                            |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| \* Executing task in folder urn\_app\_com.extensions.training: mvn clean package                                                                |                                            |
| \[INFO] skip non existing resourceDirectory D:\Work\QAD Training\Platform by Don\after review\Class 6\Dev\urn\_app\_com.extensions.training\src | est\resources                              |
| \[INFO]                                                                                                                                         |                                            |
| \[INFO] --- compiler:3.5.1:testCompile (default-testCompile) @ training-server-side-extension ---                                               |                                            |
| \[INFO] No sources to compile                                                                                                                   |                                            |
| \[INFO]                                                                                                                                         |                                            |
| \[INFO] --- surefire:3.2.5:test (default-test) @ training-server-side-extension ---                                                             |                                            |
| \[INFO] No tests to run.                                                                                                                        |                                            |
| \[INFO]                                                                                                                                         |                                            |
| \[INFO] --- jar:3.3.0:jar (default-jar) @ training-server-side-extension ---                                                                    |                                            |
| \[INFO] Building jar: D:\Work\QAD Training\Platform by Don\after review\Class 6\Dev\urn\_app\_com.extensions.training                           | arget\com.extensions.training-ext-cust.jar |
| \[INFO] ------------------------------------------------------------------------                                                                |                                            |
| \[INFO] BUILD SUCCESS                                                                                                                           |                                            |
| \[INFO] ------------------------------------------------------------------------                                                                |                                            |
| \[INFO] Total time: 3.465 s                                                                                                                     |                                            |
| \[INFO] Finished at: 2026-06-04T00:45:24+03:00                                                                                                  |                                            |
| \[INFO] ------------------------------------------------------------------------                                                                |                                            |
| \* Terminal will be reused by tasks, press any key to close it.                                                                                 |                                            |


Expected result is next: no errors in the Terminal and the notification about successful deploy of extension.

Extension building and deploying is successfully completed

40

# QAD Enterprise Platform

# Extension Example

Screenshot of the Training screen in QAD Enterprise Platform showing fields like Class Name, Location, Country, Start Date, Duration Days, Topic Type, Area of Study, Class Value, Capacity, Student Count, and Average Score. An arrow points from the Start Date field to a text box below.

For the testing, open Training screen and click New.

Pay attention that StartDate is filled by default and value is equal to current date.

QAD logo

11

# QAD Enterprise Platform

# Extension Example

QAD logo

| Purchasing<br/>Class Name | Chicago<br/>Location |
| ------------------------- | -------------------- |


Training | Students | Training Room | ⚙️

### ▾ Training

| Class Name: Purchasing               | Topic Type: Development     |
| ------------------------------------ | --------------------------- |
| Location: Chicago                    | Area of Study: Distribution |
| Country: us 🔗 🔍 UNITED STATES      | Class Value: 5              |
| Start Date: 5/11/2026 10:40 PM 📅 🕒 | Capacity: 0 \[Confirm]      |
| Duration Days: 5                     | Student Count: 9            |
| Average Score: 45.44                 |                             |


### ▾ Students

* New 🗑️ Delete More ▾

### ▾ Errors

| Field | Error                 | Error ID      |
| ----- | --------------------- | ------------- |
|       | Capacity is mandatory | JEF202606035. |


Then, select any existing record, set Capacity value to 0 and try to save record.
You should receive “Capacity is mandatory” error.
Restore Capacity value as it was originally and try to save record again, you will
see that record will be saved successfully.

42

logo

Purchasing Chicago Class Name Location Training Students Training Room ¤ Training Class Name Topic Type Purchasing Development Location Chicago Area of StudyDistribution Country α UNITED STATES Class Value 5 us Start Date 5/11/2026 10:40 PM Capacity 0Confirm Duration Days 5 Student Count 9 Average Score 4544 Students +New Delete More Errors Field Error Error ID Capacity is mandatory JEF202606035.

QAD logo

QAD Inc.

<page_number>43</page_number>