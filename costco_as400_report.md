
# Costco’s AS/400-Based Transaction & Inventory Systems  
### Technical Deep Dive

Costco Wholesale operates critical retail systems on an IBM AS/400 platform (now IBM i), originally deployed in 1988【1†L166-L174】. This legacy system runs Costco’s core transactions, inventory management, membership records, and more【24†L193-L201】. At Costco stores, employees still use green-screen 5250 terminal interfaces at point-of-sale and inventory lookup stations, underscoring the system’s continued role in daily operations【1†L166-L174】. The AS/400’s reputation for rock-solid reliability (often 99.9% uptime) and security through obscurity has made it a “fossil” that Costco deliberately preserves as a backbone of its IT strategy【1†L178-L187】【1†L189-L197】. In this report, we compile technical details – from internal architecture and database design to leaked insights from employees – about Costco’s AS/400-based transaction and inventory applications, without comparing them to newer systems.

---

## 1. System Architecture and Technology Stack

Costco’s AS/400 system functions as a centralized ERP-like environment supporting multiple retail business domains. It runs on IBM i operating system (formerly OS/400) and utilizes IBM’s integrated DB2 database for data storage【4†L349-L357】. The software is largely custom-built in IBM’s RPG programming language (RPG II/III and modern RPG ILE), accumulated over 30+ years of development and maintenance【24†L282-L290】. Hundreds of discrete programs (each identified by short alphanumeric codes) handle different functions – e.g. inventory inquiries, receiving, sign printing – all accessible through text-based menus on 5250 terminals【24†L282-L289】【33†L133-L141】.

The codebase has been continuously tweaked and “band-aided” to keep up with business needs, a fact humorously acknowledged by Costco’s former CFO who noted their IT is “always up and running, but band-aided to death”【1†L197-L204】.

### 1.1 Core Characteristics

- **Platform:** IBM AS/400 / IBM i (OS/400) on IBM Power hardware【4†L349-L357】  
- **Database:** Integrated DB2 for i, originally DDS-based physical/logical files with growing use of SQL DDL and queries【4†L349-L357】  
- **Languages:** RPG II/III, RPG ILE, SQLRPGLE for modern work, plus CL (Control Language) scripts  
- **User Interface:** 5250 green-screen terminals and emulators, fully keyboard-driven【24†L252-L261】  
- **Uptime & Security:** Extremely high reliability with minimal downtime and low exposure to common malware due to niche stack【1†L178-L187】【1†L185-L193】  

The AS/400 architecture emphasizes stability and performance. Costco’s system processes millions of daily transactions with minimal downtime【1†L178-L187】. User interaction is entirely keyboard-driven, which seasoned employees find extremely efficient for repetitive tasks compared to GUI systems【24†L252-L261】【24†L263-L270】.

Each warehouse (store) connects to the central IBM i system (or regional instances), allowing real-time updates of sales and inventory. When a sale is processed at the register, the system immediately decrements inventory on-hand and updates sales totals for that item.

### 1.2 Integration Patterns

Integration between the AS/400 applications and external or modern systems is handled through a combination of batch data syncs and real-time messaging:

- **Message-oriented integration:**  
  - Use of IBM MQ (Message Queue) for asynchronous communication with external services【42†L85-L93】  
  - RPG/SQLRPGLE programs embed XML payloads and send/receive via MQ, triggered on key events (e.g., sale posted, membership updated)【42†L85-L93】  

- **Batch exports/imports:**  
  - Nightly jobs generate flat-file extracts (or DB2 snapshots) for downstream analytics and modern BI platforms  
  - Examples include regional inventory snapshots and sales aggregates used in IA1 and reporting screens【33†L318-L327】  

- **Bridging / “shim” services:**  
  - Custom “bridge” applications sync data between the AS/400 and newer CRM or SAP components【24†L281-L289】【24†L291-L299】  
  - Issues in these bridges can cause visible operational glitches, underscoring their centrality【24†L281-L289】  

### 1.3 Snapshot & Batch Approach

Many cross-warehouse or high-level views rely on snapshot tables refreshed nightly or at scheduled intervals:

- **IA1 (regional inventory)** reads from a snapshot updated once per day and includes RTV (return-to-vendor) stock【33†L318-L327】  
- Daily and weekly reports (department sales, zero-sales lists, etc.) are produced by overnight batch processing and stored as spooled files for later printing【4†L315-L323】  

---

## 2. Database Design and Data Management

The core database is IBM DB2 for i. All enterprise data – product master records, stock levels, sales transactions, membership info, etc. – lives in DB2 tables (physical files). Historically, schema definitions used DDS; over time, SQL-based DDL and access have been layered in【4†L349-L357】.

### 2.1 Data Modeling Patterns

- **Transactional normalization:**  
  - Item masters, warehouse (location) masters, and membership masters are distinct entities  
  - Inventory is stored in item-location tables that track:  
    - On-hand quantity  
    - Quantity sold today  
    - Inbound quantities (en route vs. received)  
    - Promotional flags (coupon, markdown, etc.)【4†L351-L359】【4†L359-L367】  

- **Logical files / indexes:**  
  - Legacy design uses logical files as indexed views over physical files  
  - Examples:  
    - Alpha index by item description to support IAI (Item Alpha Inquiry)【4†L351-L359】  
    - Sorted views for membership, purchase history, and departmental reporting  

- **SQL evolution:**  
  - Costco iSeries roles explicitly call for SQL and SQLRPGLE expertise【42†L77-L85】  
  - Triggers, stored procedures, and views are used for:  
    - Derived aggregates  
    - Change capture / event generation  
    - Complex joins for BI extraction【42†L85-L93】  

### 2.2 Key Data Domains

1. **Item & Inventory**  
   - **Item master**: descriptive attributes, pack size, department, pricing, coupon flags  
   - **Item-location**: per-warehouse quantities and transactional counters  
   - **Promotions & coupons**: tables for active/queued rebates and coupons (queried by IRCI, IATOP)【33†L145-L153】【33†L303-L311】  

2. **Sales Transactions**  
   - Line-level transaction tables keyed by:  
     - Warehouse, register, transaction number, line sequence  
   - Each line references:  
     - Membership ID (if present)  
     - Item ID, quantity, price, discount/coupon applied  

3. **Membership**  
   - Membership master: member ID, status, tier, renewal date, 2% reward tracking  
   - Membership history: transactions linked to memberships (accessible via WII)【4†L363-L370】  

4. **Receiving & Logistics**  
   - Purchase orders and load manifests: linked to depots/suppliers and warehouses  
   - Receiving history tables: track checked-in quantities and dates (queried via RHI)【4†L329-L337】  

### 2.3 Batch Processing and Reporting

- **Inventory snapshots:**  
  - A nightly job consolidates item-location data across warehouses/regions  
  - IA1 reads from these snapshots and includes non-sellable stock like RTV【33†L318-L327】  

- **Sales aggregation:**  
  - Departmental and daily totals (DSI, LSDT) computed via batch jobs【23†L37-L40】  
  - Weekly zero-sales and stock status reports (WSRZS, WSRWS) generated for management review【4†L323-L331】  

- **Spool-based reporting:**  
  - Reports land in spooled output queues  
  - Users manage print/review via OUTQ:  
    - Option 5: display report on-screen  
    - Option 6: release to printer【4†L315-L323】  

### 2.4 Analytics & Warehouse Layer

Job descriptions reference normalized and denormalized schema design and star schemas as useful skills【42†L89-L97】, implying:

- A reporting/analytics layer (possibly on iSeries or offloaded) with:  
  - Fact tables for sales and inventory movements  
  - Dimension tables for items, members, warehouses, time  
- This layer is likely populated via nightly ETL from operational DB2 tables

---

## 3. Key AS/400 Applications and Modules

Costco’s AS/400 suite covers inventory, POS, receiving, signage, membership, and reporting. Most knowledge comes from employees sharing command references and usage tips on internal forums and Reddit.

### 3.1 Inventory & Item Lookup

- **IAI – Item Alpha Inquiry**【4†L351-L359】  
  - Keyword-based item search when item number is unknown  
  - Likely backed by logical files keyed on description  

- **ITMW – Item Inquiry by Item #**【4†L351-L359】【4†L359-L367】  
  - Primary inventory detail screen  
  - Shows:  
    - On-hand quantity  
    - Quantity sold today  
    - Coupons applied  
    - Inbound shipment quantities (en route vs. received)  
    - Pack size / units per pallet  

- **IA1 – Regional Inventory Snapshot**【33†L318-L327】  
  - Cross-warehouse view of item inventory across region/company  
  - Snapshot at start of day; doesn’t update until next day  
  - Includes RTV inventory, so quantities may not reflect sellable stock  

- **IATOP – Top Sellers / Top Refunds**【33†L145-L153】【33†L275-L283】  
  - Lists top-selling items, top refunds, DND items by department or warehouse  
  - Used by managers to identify high-velocity items or problem SKUs  

- **IIC – Category Sales Inquiry**【33†L147-L155】  
  - Category-level view of sales, e.g., SquareTrade warranty counts  

### 3.2 Sales & POS

- **DSI – Department Sales Inquiry**【23†L37-L40】  
  - Shows department-level sales totals  

- **LSDT – Daily Sales Total**【23†L37-L40】  
  - Daily sales summary for the warehouse  

- **WII – Membership Purchase History**【4†L363-L370】  
  - Search purchases by membership number  
  - Used at returns/membership desks to verify purchases  

In practice, POS interfaces often appear as green-screen windows that write directly into AS/400 transaction tables, updating inventory and sales in real time【1†L166-L174】.

### 3.3 Receiving & Inbound Logistics

- **WHS – Warehouse Schedule / “Hot Sheet”**【33†L141-L148】【33†L275-L283】  
  - Main view of scheduled depot deliveries  
  - Supports printing “hot sheets” to prioritize critical inbound items  
  - Links to PDIW for detailed item listings per load【33†L265-L273】  

- **DASH – Depot Appointment / Check-in**【33†L151-L159】【33†L229-L237】  
  - Shows all inbound trucks and appointments  
  - Hidden function (Shift+F4) reveals upcoming loads in detail【33†L208-L216】  
  - Supports truck check-in, typically restricted by user role【33†L160-L168】【33†L182-L190】  

- **PDIW – PO Detail Inquiry – Warehouse**【33†L242-L251】  
  - Lists items on inbound loads, filterable by load or department  
  - Used to see what arrived overnight or is slated to arrive  

- **RHI – Receiving History Inquiry**【4†L329-L337】  
  - Shows historical receiving events for an item  
  - May lag same-day receipts until posting completes【4†L331-L338】  

### 3.4 Signage & Price Management

- **EDSR – Every Day Sign Request**【33†L133-L141】  
  - Bulk sign printing for items (e.g., after price changes)  

- **EDSM – Sign Reprint / Custom Sign**【4†L297-L304】  
  - Reprints or modifies individual signs (e.g., price changes, manager notes)  
  - Common at membership desk and supervisor workstations  

- **EDMP – Daily Sign Maintenance**【4†L299-L307】  
  - Lists all sign changes for the day (coupons, markdowns, price changes)  
  - Staff must deselect items they don’t want printed to avoid massive print jobs  

- **EPCI – Permanent Markdown Inquiry**【4†L337-L344】  
  - Lists all markdown items (clearance) in the warehouse  

### 3.5 Membership & CRM

- **MBA / MBA9 – Membership Inquiry/Management**【30†L520-L528】  
  - Original MBA required separate login and had more powerful functions  
  - MBA9 is read-only membership lookup available on warehouse login  
  - Displays account status, renewal dates, rewards, etc.  

- **WII – Purchase History by Member**【4†L363-L370】  
  - Complements MBA9 for returns and customer service  

- **STOP – Disposal / Handling Guidance**【4†L369-L377】  
  - Provides instructions for disposing of particular items  
  - Rarely used in practice but shows breadth of data housed on AS/400  

### 3.6 Reporting & Miscellaneous Tools

- **MACR – On-hand Inventory Report**【33†L143-L148】【30†L473-L481】  
  - Compressed inventory report for a department  
  - Widely used by stockers and managers to plan restocking  

- **WSRWS – Weekly Stock Status**【4†L323-L331】  
  - Detailed stock report; can be enormous if run for entire warehouse  

- **WSRZS – Weekly Zero Sales**【4†L323-L331】  
  - Identifies SKUs with no sales over a period  

- **IRCI – Rebate & Coupon Inquiry**【33†L303-L311】  
  - Shows items scheduled to go on rebate before the promotion starts  

- **OUTQ – Output Queue Management**【4†L315-L323】  
  - Manages spooled reports waiting to print  

Collectively, these applications represent **hundreds** of RPG programs across the Costco enterprise【24†L282-L290】.

---

## 4. Maintenance, Reverse Engineering, and Modernization

### 4.1 Codebase Characteristics

Costco’s AS/400 codebase is a large, evolving set of RPG programs plus CL scripts:

- Written over decades, by multiple generations of developers【24†L282-L290】  
- Frequently modified to handle new business rules (“band-aided”)【1†L197-L204】  
- Highly interdependent: changes require deep cross-reference analysis【42†L89-L97】  

To manage this, Costco’s iSeries team uses:

- **TurnOver** – source change management and deployment tool【42†L89-L97】  
- **X-Analysis** – code cross-referencing and impact analysis tool【42†L89-L97】  

Job descriptions stress:

- Strong RPG, SQLRPGLE, and CL skills【42†L77-L85】  
- Experience with triggers, stored procedures, and MQ integration【42†L85-L93】  

### 4.2 Modernization Efforts

Costco has worked for years to migrate parts of the AS/400 stack to newer platforms (e.g., SAP modules, modern CRM, third-party pharmacy systems)【24†L193-L201】【24†L239-L247】. Challenges include:

- Re-writing hundreds of interlinked RPG programs from scratch【24†L282-L290】  
- Migrating very large, mission-critical datasets without disruption【24†L225-L233】  
- Maintaining operational continuity during phased cutovers  

Warehouse employees often report that newer systems are slower or less ergonomic than green-screen interfaces, and they gravitate back to AS/400 tools where possible【24†L143-L151】【24†L147-L155】.

### 4.3 Informal Documentation & Reverse Engineering

Much of the public knowledge about Costco’s AS/400 internals comes from employee posts and informal command lists. Common themes:

- Training on AS/400 is often tribal; knowledge passes via coworkers and community posts【24†L307-L314】  
- Reddit threads act as “living manuals” listing commands and gotchas【33†L133-L141】【33†L275-L283】  
- New employees initially find the system unintuitive but eventually become very fast once they learn the key screens and shortcuts【24†L252-L261】【24†L263-L270】  

From a reverse-engineering standpoint:

- No Costco AS/400 source code has leaked publicly in any significant volume  
- Architecture and schema must be inferred from:  
  - Command behavior and screen outputs  
  - IT job descriptions  
  - Employee and ex-employee descriptions  

---

## 5. Where to Find More Details (Official & Unofficial)

Below are starting points for deeper research, training yourself, or validating the architectural picture.

### 5.1 Official / Semi-Official Sources

- **IBM i / AS/400 Platform Documentation (IBM):**  
  - General architecture, DB2 for i, RPG, MQ integration, and 5250 details.  
  - Helps interpret how Costco’s environment is likely structured.  

- **Costco Technology Job Listings:**  
  - iSeries Developer / Analyst positions mentioning:  
    - RPG, SQLRPGLE, CL, MQ, triggers, stored procedures【42†L77-L85】【42†L85-L93】  
    - Use of TurnOver, X-Analysis, Robot Scheduler【42†L89-L97】  
  - These give direct signals on stack components and tooling.  

### 5.2 Unofficial / Reverse-Engineered Sources

- **Reddit – r/Costco and related threads:**  
  - Posts where employees document AS/400 commands and behavior, e.g.:  
    - Inventory commands (IAI, ITMW, IA1, IATOP, MACR, WSRWS, RHI)【4†L351-L359】【4†L329-L337】【33†L143-L148】  
    - Receiving & logistics (WHS, DASH, PDIW)【33†L141-L148】【33†L242-L251】  
    - Membership modules (MBA, MBA9, WII)【30†L520-L528】【4†L363-L370】  
    - Signage and markdown tools (EDSR, EDSM, EDMP, EPCI)【33†L133-L141】【4†L297-L307】  

- **SourceData / Trade Press Articles:**  
  - Discussions of Costco’s decision to stick with AS/400 and how it aligns with their business model【1†L166-L174】【1†L197-L204】  

- **Legacy IBM i Community Resources:**  
  - Technical blogs and forums on RPG, DB2 for i, MQ integration, and modernization patterns.  
  - While not Costco-specific, they map directly onto the tooling Costco uses.  

---

## 6. Summary

Costco’s AS/400-based systems are:

- A centralized IBM i/DB2/RPG environment running:  
  - Inventory control, POS back-end, membership, receiving, signage, and reporting  
- Architected around:  
  - Highly normalized transactional data  
  - Logical files and SQL views  
  - Robust batch processing and snapshots for regional/enterprise views  
- Integrated using:  
  - IBM MQ, XML payloads, and nightly flat-file or DB exports【42†L85-L93】  
- Maintained via:  
  - Modern tooling (TurnOver, X-Analysis) on top of deeply legacy RPG code【42†L89-L97】  

While actual source code remains proprietary, the combination of employee “field manuals,” IT job postings, and IBM i platform patterns provides enough insight to reconstruct a reasonably detailed picture of Costco’s AS/400 transaction and inventory architecture.

