-- =====================================================================
-- ACME Corp — enterprise BigQuery dataset (33 tables)
-- Schema + table & column descriptions INLINE (no ALTER rate-limit issues).
-- Run order: this file, then acme_corp_seed_data.sql.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS `acme_corp`
OPTIONS (
  description = 'ACME Corp enterprise data warehouse',
  location = 'US'
);

-- =====================================================================
-- 1. ORGANIZATION
-- =====================================================================

-- offices
CREATE OR REPLACE TABLE `acme_corp.offices` (
  office_id           STRING    NOT NULL OPTIONS(description = 'Unique office identifier (format: OFF###). Primary key.'),
  name                STRING    NOT NULL OPTIONS(description = 'Display name of the office, typically city-based (e.g. "San Francisco HQ").'),
  country             STRING    NOT NULL OPTIONS(description = 'ISO 3166-1 alpha-2 country code.'),
  city                STRING             OPTIONS(description = 'City where the office is located.'),
  address             STRING             OPTIONS(description = 'Full street address.'),
  timezone            STRING             OPTIONS(description = 'IANA timezone identifier (e.g. "America/Los_Angeles").'),
  headcount_capacity  INT64              OPTIONS(description = 'Maximum number of employees the office can seat.'),
  opened_date         DATE               OPTIONS(description = 'Date the office officially opened.'),
  is_hq               BOOL               OPTIONS(description = 'TRUE for the global headquarters. Exactly one office should have this flag set.'),
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP() OPTIONS(description = 'Row insert timestamp.'),
  PRIMARY KEY (office_id) NOT ENFORCED
)
OPTIONS (description = 'Physical ACME offices worldwide. One row per office location. Source of truth for employee work locations and regional capacity planning.');

-- departments
CREATE OR REPLACE TABLE `acme_corp.departments` (
  department_id         STRING    NOT NULL OPTIONS(description = 'Unique department identifier (format: DEPT###). Primary key.'),
  name                  STRING    NOT NULL OPTIONS(description = 'Department display name (e.g. "Engineering", "Customer Success").'),
  cost_center           STRING             OPTIONS(description = 'Finance cost center code used in GL postings.'),
  parent_department_id  STRING             OPTIONS(description = 'Logical self-reference to departments.department_id (BigQuery does not allow self-FK). NULL for top-level departments.'),
  head_employee_id      STRING             OPTIONS(description = 'Logical FK to employees.employee_id. The department head / senior leader.'),
  budget_annual_usd     NUMERIC            OPTIONS(description = 'Approved annual operating budget in USD.'),
  created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP() OPTIONS(description = 'Row insert timestamp.'),
  PRIMARY KEY (department_id) NOT ENFORCED
)
OPTIONS (description = 'Organizational departments. Self-referencing via parent_department_id to form the department tree. Cost centers map to finance GL codes.');

-- teams
CREATE OR REPLACE TABLE `acme_corp.teams` (
  team_id           STRING   NOT NULL OPTIONS(description = 'Unique team identifier (format: TEAM###). Primary key.'),
  name              STRING   NOT NULL OPTIONS(description = 'Team display name (e.g. "Platform", "Enterprise Sales").'),
  department_id     STRING   NOT NULL OPTIONS(description = 'FK to departments.department_id.'),
  lead_employee_id  STRING            OPTIONS(description = 'FK to employees.employee_id. Team lead / manager.'),
  slack_channel     STRING            OPTIONS(description = 'Primary Slack channel for the team (includes leading "#").'),
  formed_date       DATE              OPTIONS(description = 'Date the team was formally created.'),
  is_active         BOOL              OPTIONS(description = 'FALSE if the team has been dissolved / reorganized away.'),
  PRIMARY KEY (team_id) NOT ENFORCED,
  FOREIGN KEY (department_id) REFERENCES `acme_corp.departments`(department_id) NOT ENFORCED
)
OPTIONS (description = 'Teams within departments. A department typically has multiple teams. Used for squad-level reporting and Slack routing.');

-- job_titles
CREATE OR REPLACE TABLE `acme_corp.job_titles` (
  job_title_id  STRING  NOT NULL OPTIONS(description = 'Unique job title identifier (format: JT###). Primary key.'),
  title         STRING  NOT NULL OPTIONS(description = 'Human-readable title (e.g. "Senior Software Engineer").'),
  level         STRING           OPTIONS(description = 'Career level code. IC1..IC8 for individual contributors, M1..M5 for managers.'),
  job_family    STRING           OPTIONS(description = 'Job family grouping: engineering, sales, product, customer_success, g_and_a.'),
  min_salary    NUMERIC          OPTIONS(description = 'Bottom of the salary band in the specified currency.'),
  max_salary    NUMERIC          OPTIONS(description = 'Top of the salary band in the specified currency.'),
  currency      STRING           OPTIONS(description = 'ISO 4217 currency code for the salary band.'),
  PRIMARY KEY (job_title_id) NOT ENFORCED
)
OPTIONS (description = 'Canonical job titles with level and salary band. Employees reference this table to avoid free-text title drift.');

-- employees
CREATE OR REPLACE TABLE `acme_corp.employees` (
  employee_id        STRING    NOT NULL OPTIONS(description = 'Unique employee identifier (format: EMP###). Primary key. Stable across role changes.'),
  first_name         STRING    NOT NULL OPTIONS(description = 'Employee legal first name.'),
  last_name          STRING    NOT NULL OPTIONS(description = 'Employee legal last name.'),
  email              STRING    NOT NULL OPTIONS(description = 'Corporate email address. Unique per active employee.'),
  phone              STRING             OPTIONS(description = 'Work phone number in E.164 format.'),
  hire_date          DATE      NOT NULL OPTIONS(description = 'Date the employee started at ACME.'),
  termination_date   DATE               OPTIONS(description = 'Last working day. NULL for active employees.'),
  employment_status  STRING             OPTIONS(description = 'Current status: active, terminated, on_leave.'),
  employment_type    STRING             OPTIONS(description = 'Employment category: full_time, part_time, contractor.'),
  manager_id         STRING             OPTIONS(description = 'Logical self-reference to employees.employee_id (BigQuery does not allow self-FK). Direct manager; NULL for C-level.'),
  department_id      STRING             OPTIONS(description = 'FK to departments.department_id.'),
  team_id            STRING             OPTIONS(description = 'FK to teams.team_id. Optional (not every employee belongs to a team).'),
  job_title_id       STRING             OPTIONS(description = 'FK to job_titles.job_title_id. Current title.'),
  office_id          STRING             OPTIONS(description = 'FK to offices.office_id. Primary assigned office (remote employees keep a nominal office).'),
  date_of_birth      DATE               OPTIONS(description = 'Date of birth. Sensitive PII — access-controlled.'),
  gender             STRING             OPTIONS(description = 'Self-reported gender. Sensitive PII.'),
  country            STRING             OPTIONS(description = 'ISO 3166-1 alpha-2 country of residence for tax purposes.'),
  emergency_contact  STRUCT<name STRING, relation STRING, phone STRING> OPTIONS(description = 'STRUCT with name, relation, phone for emergency contact. Sensitive PII.'),
  skills             ARRAY<STRING>      OPTIONS(description = 'ARRAY of skill tags, self-reported or inferred from HR tools.'),
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP() OPTIONS(description = 'Row insert timestamp.'),
  updated_at         TIMESTAMP          OPTIONS(description = 'Last update timestamp. Bumped on any row change.'),
  PRIMARY KEY (employee_id) NOT ENFORCED,
  FOREIGN KEY (department_id)  REFERENCES `acme_corp.departments`(department_id)   NOT ENFORCED,
  FOREIGN KEY (team_id)        REFERENCES `acme_corp.teams`(team_id)               NOT ENFORCED,
  FOREIGN KEY (job_title_id)   REFERENCES `acme_corp.job_titles`(job_title_id)     NOT ENFORCED,
  FOREIGN KEY (office_id)      REFERENCES `acme_corp.offices`(office_id)           NOT ENFORCED
)
CLUSTER BY department_id, employment_status
OPTIONS (description = 'All ACME employees, past and present. Contains current role snapshot; see employee_role_history for time-series role changes. Clustered by department_id, employment_status.');

-- employee_role_history
CREATE OR REPLACE TABLE `acme_corp.employee_role_history` (
  role_history_id  STRING  NOT NULL OPTIONS(description = 'Unique role history record (format: RH###). Primary key.'),
  employee_id      STRING  NOT NULL OPTIONS(description = 'FK to employees.employee_id.'),
  job_title_id     STRING  NOT NULL OPTIONS(description = 'FK to job_titles.job_title_id. Title held during this period.'),
  department_id    STRING           OPTIONS(description = 'FK to departments.department_id during this period.'),
  team_id          STRING           OPTIONS(description = 'FK to teams.team_id during this period.'),
  manager_id       STRING           OPTIONS(description = 'FK to employees.employee_id. Manager during this period.'),
  start_date       DATE    NOT NULL OPTIONS(description = 'First day in this role.'),
  end_date         DATE             OPTIONS(description = 'Last day in this role. NULL for the current role.'),
  change_reason    STRING           OPTIONS(description = 'Why the change happened: new_hire, promotion, lateral, reorg, termination.'),
  PRIMARY KEY (role_history_id) NOT ENFORCED,
  FOREIGN KEY (employee_id)  REFERENCES `acme_corp.employees`(employee_id)   NOT ENFORCED,
  FOREIGN KEY (job_title_id) REFERENCES `acme_corp.job_titles`(job_title_id) NOT ENFORCED
)
OPTIONS (description = 'SCD-style time-series of employee role changes. One row per role held. end_date IS NULL for the current role. Used for tenure, promotion velocity, and reorg analysis.');

-- compensation
CREATE OR REPLACE TABLE `acme_corp.compensation` (
  compensation_id    STRING   NOT NULL OPTIONS(description = 'Unique comp record (format: COMP###). Primary key.'),
  employee_id        STRING   NOT NULL OPTIONS(description = 'FK to employees.employee_id.'),
  effective_date     DATE     NOT NULL OPTIONS(description = 'Date the comp change takes effect. Table is partitioned on this column.'),
  base_salary        NUMERIC           OPTIONS(description = 'Annualized base salary in the specified currency.'),
  bonus_target_pct   NUMERIC           OPTIONS(description = 'Target bonus as a percentage of base salary.'),
  equity_grant_usd   NUMERIC           OPTIONS(description = 'Equity grant value in USD at grant time. 0 for cash-only roles.'),
  currency           STRING            OPTIONS(description = 'ISO 4217 currency code.'),
  change_type        STRING            OPTIONS(description = 'Reason for the change: new_hire, merit, promotion, adjustment.'),
  approved_by        STRING            OPTIONS(description = 'FK to employees.employee_id of the approver.'),
  PRIMARY KEY (compensation_id) NOT ENFORCED,
  FOREIGN KEY (employee_id) REFERENCES `acme_corp.employees`(employee_id) NOT ENFORCED
)
PARTITION BY effective_date
CLUSTER BY employee_id
OPTIONS (description = 'Compensation change history. One row per comp event (new hire, merit, promotion, adjustment). Partitioned by effective_date, clustered by employee_id. Highly sensitive — restricted access.');

-- performance_reviews
CREATE OR REPLACE TABLE `acme_corp.performance_reviews` (
  review_id              STRING    NOT NULL OPTIONS(description = 'Unique review identifier (format: REV###). Primary key.'),
  employee_id            STRING    NOT NULL OPTIONS(description = 'FK to employees.employee_id. The reviewee.'),
  reviewer_id            STRING    NOT NULL OPTIONS(description = 'FK to employees.employee_id. The reviewer (typically the manager).'),
  review_period          STRING             OPTIONS(description = 'Review period label, e.g. "2025-H1".'),
  overall_rating         STRING             OPTIONS(description = 'Categorical rating: exceeds, meets, below.'),
  numeric_score          NUMERIC            OPTIONS(description = 'Numeric score on a 1.0-5.0 scale.'),
  strengths              STRING             OPTIONS(description = 'Free-text strengths noted by the reviewer.'),
  areas_for_improvement  STRING             OPTIONS(description = 'Free-text development areas.'),
  submitted_at           TIMESTAMP          OPTIONS(description = 'When the review was finalized and submitted.'),
  PRIMARY KEY (review_id) NOT ENFORCED,
  FOREIGN KEY (employee_id) REFERENCES `acme_corp.employees`(employee_id) NOT ENFORCED,
  FOREIGN KEY (reviewer_id) REFERENCES `acme_corp.employees`(employee_id) NOT ENFORCED
)
OPTIONS (description = 'Half-yearly performance reviews. One row per employee per review period.');

-- time_off_requests
CREATE OR REPLACE TABLE `acme_corp.time_off_requests` (
  request_id    STRING    NOT NULL OPTIONS(description = 'Unique request identifier (format: TOR###). Primary key.'),
  employee_id   STRING    NOT NULL OPTIONS(description = 'FK to employees.employee_id. The requester.'),
  request_type  STRING             OPTIONS(description = 'Type of leave: vacation, sick, parental, bereavement.'),
  start_date    DATE               OPTIONS(description = 'First day of leave. Table is partitioned on this column.'),
  end_date      DATE               OPTIONS(description = 'Last day of leave (inclusive).'),
  total_days    NUMERIC            OPTIONS(description = 'Business days requested. May include half-days (NUMERIC).'),
  status        STRING             OPTIONS(description = 'Request state: pending, approved, denied, cancelled.'),
  approver_id   STRING             OPTIONS(description = 'FK to employees.employee_id of the approver.'),
  requested_at  TIMESTAMP          OPTIONS(description = 'When the request was submitted.'),
  PRIMARY KEY (request_id) NOT ENFORCED,
  FOREIGN KEY (employee_id) REFERENCES `acme_corp.employees`(employee_id) NOT ENFORCED
)
PARTITION BY start_date
OPTIONS (description = 'Employee time-off requests. Partitioned by start_date.');

-- training_courses
CREATE OR REPLACE TABLE `acme_corp.training_courses` (
  course_id       STRING    NOT NULL OPTIONS(description = 'Unique course identifier (format: CRS###). Primary key.'),
  title           STRING    NOT NULL OPTIONS(description = 'Course title.'),
  provider        STRING             OPTIONS(description = 'Course provider (e.g. "Internal", "Neo4j Academy", "DataCamp").'),
  category        STRING             OPTIONS(description = 'Category: compliance, engineering, leadership, sales, analytics.'),
  duration_hours  NUMERIC            OPTIONS(description = 'Expected course duration in hours.'),
  is_mandatory    BOOL               OPTIONS(description = 'TRUE if required of all employees (e.g. compliance training).'),
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP() OPTIONS(description = 'Row insert timestamp.'),
  PRIMARY KEY (course_id) NOT ENFORCED
)
OPTIONS (description = 'Catalog of training courses available to employees, internal or external.');

-- employee_training
CREATE OR REPLACE TABLE `acme_corp.employee_training` (
  enrollment_id      STRING    NOT NULL OPTIONS(description = 'Unique enrollment identifier (format: ENR###). Primary key.'),
  employee_id        STRING    NOT NULL OPTIONS(description = 'FK to employees.employee_id.'),
  course_id          STRING    NOT NULL OPTIONS(description = 'FK to training_courses.course_id.'),
  enrolled_at        TIMESTAMP          OPTIONS(description = 'When the employee enrolled.'),
  completed_at       TIMESTAMP          OPTIONS(description = 'When the employee completed the course. NULL if in progress or abandoned.'),
  completion_status  STRING             OPTIONS(description = 'Status: completed, in_progress, abandoned.'),
  score              NUMERIC            OPTIONS(description = 'Final score (0-100). NULL if no assessment or not completed.'),
  PRIMARY KEY (enrollment_id) NOT ENFORCED,
  FOREIGN KEY (employee_id) REFERENCES `acme_corp.employees`(employee_id)        NOT ENFORCED,
  FOREIGN KEY (course_id)   REFERENCES `acme_corp.training_courses`(course_id)  NOT ENFORCED
)
OPTIONS (description = 'Junction table tracking employee enrollments in training courses.');

-- =====================================================================
-- 2. CUSTOMERS
-- =====================================================================

-- customers
CREATE OR REPLACE TABLE `acme_corp.customers` (
  customer_id         STRING    NOT NULL OPTIONS(description = 'Unique customer account identifier (format: CUST###). Primary key.'),
  company_name        STRING    NOT NULL OPTIONS(description = 'Legal company name.'),
  industry            STRING             OPTIONS(description = 'Industry vertical (e.g. financial_services, retail, healthcare).'),
  annual_revenue_usd  NUMERIC            OPTIONS(description = 'Estimated customer annual revenue in USD, from enrichment data.'),
  employee_count      INT64              OPTIONS(description = 'Estimated customer employee count.'),
  website             STRING             OPTIONS(description = 'Customer primary website domain.'),
  country             STRING             OPTIONS(description = 'ISO 3166-1 alpha-2 headquarters country.'),
  segment             STRING             OPTIONS(description = 'Sales segment: enterprise, mid_market, smb.'),
  acquired_date       DATE               OPTIONS(description = 'Date the customer signed the first contract.'),
  account_owner_id    STRING             OPTIONS(description = 'FK to employees.employee_id. Current account owner (AE or CSM).'),
  status              STRING             OPTIONS(description = 'Account status: active, churned, prospect.'),
  lifetime_value_usd  NUMERIC            OPTIONS(description = 'Cumulative revenue from this customer to date, in USD.'),
  health_score        NUMERIC            OPTIONS(description = 'Account health score 0-100. Computed by Customer Success model.'),
  tags                ARRAY<STRING>      OPTIONS(description = 'ARRAY of free-form tags (e.g. "strategic", "at_risk", "case_study").'),
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP() OPTIONS(description = 'Row insert timestamp.'),
  PRIMARY KEY (customer_id) NOT ENFORCED,
  FOREIGN KEY (account_owner_id) REFERENCES `acme_corp.employees`(employee_id) NOT ENFORCED
)
CLUSTER BY segment, status
OPTIONS (description = 'B2B customer accounts. One row per company (logo). Clustered by segment, status. Source of truth for account ownership and LTV.');

-- customer_contacts
CREATE OR REPLACE TABLE `acme_corp.customer_contacts` (
  contact_id         STRING    NOT NULL OPTIONS(description = 'Unique contact identifier (format: CONTACT###). Primary key.'),
  customer_id        STRING    NOT NULL OPTIONS(description = 'FK to customers.customer_id.'),
  first_name         STRING             OPTIONS(description = 'Contact first name.'),
  last_name          STRING             OPTIONS(description = 'Contact last name.'),
  email              STRING             OPTIONS(description = 'Contact work email.'),
  phone              STRING             OPTIONS(description = 'Contact phone in E.164 format.'),
  title              STRING             OPTIONS(description = 'Contact job title at the customer.'),
  is_primary         BOOL               OPTIONS(description = 'TRUE for the primary account contact. At most one per customer.'),
  is_decision_maker  BOOL               OPTIONS(description = 'TRUE if the contact has buying authority.'),
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP() OPTIONS(description = 'Row insert timestamp.'),
  PRIMARY KEY (contact_id) NOT ENFORCED,
  FOREIGN KEY (customer_id) REFERENCES `acme_corp.customers`(customer_id) NOT ENFORCED
)
OPTIONS (description = 'People at customer accounts. Multiple contacts per customer. is_primary identifies the main point of contact; is_decision_maker flags economic buyers.');

-- customer_addresses
CREATE OR REPLACE TABLE `acme_corp.customer_addresses` (
  address_id    STRING NOT NULL OPTIONS(description = 'Unique address identifier (format: ADDR###). Primary key.'),
  customer_id   STRING NOT NULL OPTIONS(description = 'FK to customers.customer_id.'),
  address_type  STRING          OPTIONS(description = 'Address type: billing, shipping, hq.'),
  line1         STRING          OPTIONS(description = 'Street address line 1.'),
  line2         STRING          OPTIONS(description = 'Street address line 2 (suite, floor). May be NULL.'),
  city          STRING          OPTIONS(description = 'City.'),
  region        STRING          OPTIONS(description = 'State / province / region.'),
  postal_code   STRING          OPTIONS(description = 'Postal or ZIP code.'),
  country       STRING          OPTIONS(description = 'ISO 3166-1 alpha-2 country code.'),
  is_primary    BOOL            OPTIONS(description = 'TRUE for the primary address of this type.'),
  PRIMARY KEY (address_id) NOT ENFORCED,
  FOREIGN KEY (customer_id) REFERENCES `acme_corp.customers`(customer_id) NOT ENFORCED
)
OPTIONS (description = 'Addresses for customer accounts. Multiple addresses per customer (billing, shipping, HQ).');

-- =====================================================================
-- 3. SALES / CRM
-- =====================================================================

-- campaigns
CREATE OR REPLACE TABLE `acme_corp.campaigns` (
  campaign_id        STRING   NOT NULL OPTIONS(description = 'Unique campaign identifier (format: CAMP###). Primary key.'),
  name               STRING            OPTIONS(description = 'Campaign display name.'),
  channel            STRING            OPTIONS(description = 'Channel: email, social, paid_search, event, content, ads.'),
  start_date         DATE              OPTIONS(description = 'Campaign start date.'),
  end_date           DATE              OPTIONS(description = 'Campaign end date.'),
  budget_usd         NUMERIC           OPTIONS(description = 'Planned budget in USD.'),
  spend_usd          NUMERIC           OPTIONS(description = 'Actual spend to date in USD.'),
  owner_employee_id  STRING            OPTIONS(description = 'FK to employees.employee_id of the campaign owner.'),
  PRIMARY KEY (campaign_id) NOT ENFORCED,
  FOREIGN KEY (owner_employee_id) REFERENCES `acme_corp.employees`(employee_id) NOT ENFORCED
)
OPTIONS (description = 'Marketing campaigns across channels. Budget vs spend tracks overrun. Links to leads via leads.campaign_id.');

-- leads
CREATE OR REPLACE TABLE `acme_corp.leads` (
  lead_id               STRING    NOT NULL OPTIONS(description = 'Unique lead identifier (format: LEAD###). Primary key.'),
  first_name            STRING             OPTIONS(description = 'Lead first name.'),
  last_name             STRING             OPTIONS(description = 'Lead last name.'),
  email                 STRING             OPTIONS(description = 'Lead email address.'),
  company               STRING             OPTIONS(description = 'Free-text company name as provided by the lead.'),
  title                 STRING             OPTIONS(description = 'Job title as provided.'),
  source                STRING             OPTIONS(description = 'Lead source: web, event, referral, outbound, ads, social.'),
  campaign_id           STRING             OPTIONS(description = 'FK to campaigns.campaign_id. NULL for unattributed leads.'),
  status                STRING             OPTIONS(description = 'Lead state: new, contacted, qualified, disqualified, converted.'),
  score                 INT64              OPTIONS(description = 'Lead score 0-100 from the marketing automation platform.'),
  assigned_to           STRING             OPTIONS(description = 'FK to employees.employee_id of the assigned SDR/AE.'),
  created_at            TIMESTAMP          OPTIONS(description = 'When the lead was first captured. Partition key (by DATE).'),
  converted_customer_id STRING             OPTIONS(description = 'FK to customers.customer_id if the lead converted. NULL otherwise.'),
  converted_at          TIMESTAMP          OPTIONS(description = 'When the lead was converted.'),
  PRIMARY KEY (lead_id) NOT ENFORCED,
  FOREIGN KEY (campaign_id)           REFERENCES `acme_corp.campaigns`(campaign_id)   NOT ENFORCED,
  FOREIGN KEY (assigned_to)           REFERENCES `acme_corp.employees`(employee_id)   NOT ENFORCED,
  FOREIGN KEY (converted_customer_id) REFERENCES `acme_corp.customers`(customer_id)   NOT ENFORCED
)
PARTITION BY DATE(created_at)
CLUSTER BY status
OPTIONS (description = 'Top-of-funnel leads prior to qualification. Partitioned by DATE(created_at), clustered by status. Converts to customers via converted_customer_id.');

-- opportunities
CREATE OR REPLACE TABLE `acme_corp.opportunities` (
  opportunity_id     STRING    NOT NULL OPTIONS(description = 'Unique opportunity identifier (format: OPP###). Primary key.'),
  customer_id        STRING             OPTIONS(description = 'FK to customers.customer_id.'),
  name               STRING             OPTIONS(description = 'Opportunity display name.'),
  stage              STRING             OPTIONS(description = 'Pipeline stage: discovery, proposal, negotiation, closed_won, closed_lost.'),
  amount_usd         NUMERIC            OPTIONS(description = 'Expected deal size in USD.'),
  probability        NUMERIC            OPTIONS(description = 'Win probability 0.0-1.0. Drives weighted pipeline.'),
  close_date         DATE               OPTIONS(description = 'Expected or actual close date. Partition key.'),
  owner_employee_id  STRING             OPTIONS(description = 'FK to employees.employee_id. Deal owner (AE).'),
  source_lead_id     STRING             OPTIONS(description = 'FK to leads.lead_id if this opp originated from a tracked lead.'),
  loss_reason        STRING             OPTIONS(description = 'Free-text loss reason. Populated only for closed_lost.'),
  created_at         TIMESTAMP          OPTIONS(description = 'When the opportunity was created.'),
  closed_at          TIMESTAMP          OPTIONS(description = 'When the opportunity was closed (won or lost).'),
  PRIMARY KEY (opportunity_id) NOT ENFORCED,
  FOREIGN KEY (customer_id)        REFERENCES `acme_corp.customers`(customer_id)   NOT ENFORCED,
  FOREIGN KEY (owner_employee_id)  REFERENCES `acme_corp.employees`(employee_id)   NOT ENFORCED,
  FOREIGN KEY (source_lead_id)     REFERENCES `acme_corp.leads`(lead_id)           NOT ENFORCED
)
PARTITION BY close_date
CLUSTER BY stage
OPTIONS (description = 'Sales opportunities (deals). Partitioned by close_date, clustered by stage. Core pipeline and forecast table.');

-- sales_activities
CREATE OR REPLACE TABLE `acme_corp.sales_activities` (
  activity_id       STRING    NOT NULL OPTIONS(description = 'Unique activity identifier (format: ACT###). Primary key.'),
  opportunity_id    STRING             OPTIONS(description = 'FK to opportunities.opportunity_id. NULL for lead-only activities.'),
  lead_id           STRING             OPTIONS(description = 'FK to leads.lead_id. NULL for opportunity-stage activities.'),
  contact_id        STRING             OPTIONS(description = 'FK to customer_contacts.contact_id.'),
  employee_id       STRING             OPTIONS(description = 'FK to employees.employee_id. The rep logging the activity.'),
  activity_type     STRING             OPTIONS(description = 'Type: call, email, meeting, demo.'),
  subject           STRING             OPTIONS(description = 'Short subject / title.'),
  notes             STRING             OPTIONS(description = 'Free-text activity notes.'),
  activity_at       TIMESTAMP          OPTIONS(description = 'When the activity occurred. Partition key (by DATE).'),
  duration_minutes  INT64              OPTIONS(description = 'Activity duration in minutes.'),
  PRIMARY KEY (activity_id) NOT ENFORCED,
  FOREIGN KEY (opportunity_id) REFERENCES `acme_corp.opportunities`(opportunity_id)  NOT ENFORCED,
  FOREIGN KEY (lead_id)        REFERENCES `acme_corp.leads`(lead_id)                 NOT ENFORCED,
  FOREIGN KEY (contact_id)     REFERENCES `acme_corp.customer_contacts`(contact_id)  NOT ENFORCED,
  FOREIGN KEY (employee_id)    REFERENCES `acme_corp.employees`(employee_id)         NOT ENFORCED
)
PARTITION BY DATE(activity_at)
OPTIONS (description = 'Logged sales activities: calls, emails, meetings, demos. Partitioned by DATE(activity_at). Can link to opportunity, lead, or contact.');

-- quotes
CREATE OR REPLACE TABLE `acme_corp.quotes` (
  quote_id          STRING    NOT NULL OPTIONS(description = 'Unique quote identifier (format: Q###). Primary key.'),
  opportunity_id    STRING    NOT NULL OPTIONS(description = 'FK to opportunities.opportunity_id.'),
  version           INT64              OPTIONS(description = 'Quote version (1-based). Incremented on each revision.'),
  total_amount_usd  NUMERIC            OPTIONS(description = 'Total quote amount after discount, in USD.'),
  discount_pct      NUMERIC            OPTIONS(description = 'Discount percentage applied to list.'),
  valid_until       DATE               OPTIONS(description = 'Quote expiration date.'),
  status            STRING             OPTIONS(description = 'Quote status: draft, sent, accepted, rejected, expired.'),
  sent_at           TIMESTAMP          OPTIONS(description = 'When the quote was sent to the customer.'),
  created_by        STRING             OPTIONS(description = 'FK to employees.employee_id of the quote author.'),
  PRIMARY KEY (quote_id) NOT ENFORCED,
  FOREIGN KEY (opportunity_id) REFERENCES `acme_corp.opportunities`(opportunity_id)  NOT ENFORCED,
  FOREIGN KEY (created_by)     REFERENCES `acme_corp.employees`(employee_id)         NOT ENFORCED
)
OPTIONS (description = 'Price quotes generated against opportunities. Version increments on each revision; the highest-version accepted row represents the final deal.');

-- =====================================================================
-- 4. PRODUCTS, ORDERS, BILLING
-- =====================================================================

-- product_categories
CREATE OR REPLACE TABLE `acme_corp.product_categories` (
  category_id         STRING  NOT NULL OPTIONS(description = 'Unique category identifier (format: CAT###). Primary key.'),
  name                STRING  NOT NULL OPTIONS(description = 'Category display name.'),
  parent_category_id  STRING           OPTIONS(description = 'Logical self-reference to product_categories.category_id (BigQuery does not allow self-FK). NULL for top-level categories.'),
  description         STRING           OPTIONS(description = 'Free-text category description.'),
  PRIMARY KEY (category_id) NOT ENFORCED
)
OPTIONS (description = 'Product category tree. Self-referencing via parent_category_id.');

-- products
CREATE OR REPLACE TABLE `acme_corp.products` (
  product_id       STRING   NOT NULL OPTIONS(description = 'Unique product identifier (format: PROD###). Primary key.'),
  sku              STRING            OPTIONS(description = 'SKU code used in billing systems.'),
  name             STRING   NOT NULL OPTIONS(description = 'Product display name.'),
  category_id      STRING            OPTIONS(description = 'FK to product_categories.category_id.'),
  description      STRING            OPTIONS(description = 'Product description for marketing and sales collateral.'),
  list_price_usd   NUMERIC           OPTIONS(description = 'Standard list price in USD (pre-discount).'),
  cost_usd         NUMERIC           OPTIONS(description = 'Internal unit cost in USD. Used for gross margin.'),
  is_active        BOOL              OPTIONS(description = 'FALSE if the product is retired / not sellable.'),
  tags             ARRAY<STRING>     OPTIONS(description = 'ARRAY of product tags used for grouping (e.g. "saas", "on_prem", "genai").'),
  launched_at      DATE              OPTIONS(description = 'Date the product went GA.'),
  PRIMARY KEY (product_id) NOT ENFORCED,
  FOREIGN KEY (category_id) REFERENCES `acme_corp.product_categories`(category_id) NOT ENFORCED
)
OPTIONS (description = 'Sellable products and services. Includes software (on-prem + SaaS), services, and training. Cost is internal unit cost for margin analysis.');

-- subscriptions
CREATE OR REPLACE TABLE `acme_corp.subscriptions` (
  subscription_id    STRING   NOT NULL OPTIONS(description = 'Unique subscription identifier (format: SUB###). Primary key.'),
  customer_id        STRING   NOT NULL OPTIONS(description = 'FK to customers.customer_id.'),
  product_id         STRING   NOT NULL OPTIONS(description = 'FK to products.product_id.'),
  plan_name          STRING            OPTIONS(description = 'Plan tier name (e.g. "Enterprise Tier 3", "Cloud Growth").'),
  seats              INT64             OPTIONS(description = 'Number of seats / licenses purchased.'),
  mrr_usd            NUMERIC           OPTIONS(description = 'Monthly recurring revenue in USD.'),
  arr_usd            NUMERIC           OPTIONS(description = 'Annual recurring revenue in USD. Typically mrr_usd * 12.'),
  billing_cycle      STRING            OPTIONS(description = 'Billing cadence: monthly, annual.'),
  start_date         DATE              OPTIONS(description = 'Subscription start date. Partition key.'),
  renewal_date       DATE              OPTIONS(description = 'Next renewal date.'),
  cancelled_date     DATE              OPTIONS(description = 'Cancellation date. NULL for active subs.'),
  status             STRING            OPTIONS(description = 'Status: active, cancelled, past_due, trialing.'),
  owner_employee_id  STRING            OPTIONS(description = 'FK to employees.employee_id. Account owner (CSM).'),
  PRIMARY KEY (subscription_id) NOT ENFORCED,
  FOREIGN KEY (customer_id)       REFERENCES `acme_corp.customers`(customer_id)   NOT ENFORCED,
  FOREIGN KEY (product_id)        REFERENCES `acme_corp.products`(product_id)     NOT ENFORCED,
  FOREIGN KEY (owner_employee_id) REFERENCES `acme_corp.employees`(employee_id)   NOT ENFORCED
)
PARTITION BY start_date
CLUSTER BY status
OPTIONS (description = 'SaaS subscriptions (recurring revenue). Partitioned by start_date, clustered by status. Source of truth for MRR/ARR.');

-- orders
CREATE OR REPLACE TABLE `acme_corp.orders` (
  order_id              STRING   NOT NULL OPTIONS(description = 'Unique order identifier (format: ORD###). Primary key.'),
  customer_id           STRING   NOT NULL OPTIONS(description = 'FK to customers.customer_id.'),
  order_date            DATE              OPTIONS(description = 'Date the order was placed. Partition key.'),
  status                STRING            OPTIONS(description = 'Status: pending, shipped, delivered, cancelled, returned.'),
  currency              STRING            OPTIONS(description = 'ISO 4217 currency code. Amounts are stored in USD equivalents.'),
  subtotal_usd          NUMERIC           OPTIONS(description = 'Sum of line items before tax and shipping, USD.'),
  tax_usd               NUMERIC           OPTIONS(description = 'Total tax, USD.'),
  shipping_usd          NUMERIC           OPTIONS(description = 'Shipping fee, USD. 0 for digital-only orders.'),
  total_usd             NUMERIC           OPTIONS(description = 'Grand total in USD (subtotal + tax + shipping).'),
  placed_by_contact_id  STRING            OPTIONS(description = 'FK to customer_contacts.contact_id. The customer-side purchaser.'),
  sales_rep_id          STRING            OPTIONS(description = 'FK to employees.employee_id. The ACME sales rep.'),
  PRIMARY KEY (order_id) NOT ENFORCED,
  FOREIGN KEY (customer_id)          REFERENCES `acme_corp.customers`(customer_id)           NOT ENFORCED,
  FOREIGN KEY (placed_by_contact_id) REFERENCES `acme_corp.customer_contacts`(contact_id)    NOT ENFORCED,
  FOREIGN KEY (sales_rep_id)         REFERENCES `acme_corp.employees`(employee_id)           NOT ENFORCED
)
PARTITION BY order_date
CLUSTER BY status
OPTIONS (description = 'One-time orders (non-subscription). Partitioned by order_date, clustered by status. Includes services and perpetual licenses.');

-- order_items
CREATE OR REPLACE TABLE `acme_corp.order_items` (
  order_item_id    STRING   NOT NULL OPTIONS(description = 'Unique line item identifier (format: OI###). Primary key.'),
  order_id         STRING   NOT NULL OPTIONS(description = 'FK to orders.order_id.'),
  product_id       STRING   NOT NULL OPTIONS(description = 'FK to products.product_id.'),
  quantity         INT64             OPTIONS(description = 'Units ordered.'),
  unit_price_usd   NUMERIC           OPTIONS(description = 'Pre-discount unit price in USD at time of order.'),
  discount_pct     NUMERIC           OPTIONS(description = 'Discount percentage applied to this line.'),
  line_total_usd   NUMERIC           OPTIONS(description = 'Post-discount line total, USD.'),
  PRIMARY KEY (order_item_id) NOT ENFORCED,
  FOREIGN KEY (order_id)   REFERENCES `acme_corp.orders`(order_id)     NOT ENFORCED,
  FOREIGN KEY (product_id) REFERENCES `acme_corp.products`(product_id) NOT ENFORCED
)
OPTIONS (description = 'Line items on orders. Multiple rows per order.');

-- invoices
CREATE OR REPLACE TABLE `acme_corp.invoices` (
  invoice_id       STRING    NOT NULL OPTIONS(description = 'Unique invoice identifier (format: INV###). Primary key.'),
  customer_id      STRING    NOT NULL OPTIONS(description = 'FK to customers.customer_id.'),
  subscription_id  STRING             OPTIONS(description = 'FK to subscriptions.subscription_id. NULL for one-time order invoices.'),
  order_id         STRING             OPTIONS(description = 'FK to orders.order_id. NULL for pure-subscription invoices.'),
  invoice_number   STRING             OPTIONS(description = 'Human-readable invoice number (e.g. "INV-2025-00001"). Printed on the invoice.'),
  issue_date       DATE               OPTIONS(description = 'Date the invoice was issued. Partition key.'),
  due_date         DATE               OPTIONS(description = 'Payment due date (typically net 30).'),
  amount_usd       NUMERIC            OPTIONS(description = 'Pre-tax amount, USD.'),
  tax_usd          NUMERIC            OPTIONS(description = 'Tax amount, USD.'),
  total_usd        NUMERIC            OPTIONS(description = 'Total invoice amount in USD.'),
  status           STRING             OPTIONS(description = 'Invoice status: draft, sent, paid, overdue, void.'),
  paid_at          TIMESTAMP          OPTIONS(description = 'When the invoice was marked paid. NULL for unpaid invoices.'),
  PRIMARY KEY (invoice_id) NOT ENFORCED,
  FOREIGN KEY (customer_id)     REFERENCES `acme_corp.customers`(customer_id)         NOT ENFORCED,
  FOREIGN KEY (subscription_id) REFERENCES `acme_corp.subscriptions`(subscription_id) NOT ENFORCED,
  FOREIGN KEY (order_id)        REFERENCES `acme_corp.orders`(order_id)               NOT ENFORCED
)
PARTITION BY issue_date
CLUSTER BY status
OPTIONS (description = 'Invoices issued to customers. Partitioned by issue_date, clustered by status. Linked to subscription or order (or both).');

-- payments
CREATE OR REPLACE TABLE `acme_corp.payments` (
  payment_id                STRING    NOT NULL OPTIONS(description = 'Unique payment identifier (format: PAY###). Primary key.'),
  invoice_id                STRING    NOT NULL OPTIONS(description = 'FK to invoices.invoice_id.'),
  customer_id               STRING    NOT NULL OPTIONS(description = 'FK to customers.customer_id. Denormalized for query performance.'),
  payment_method            STRING             OPTIONS(description = 'Method: card, ach, wire, check.'),
  amount_usd                NUMERIC            OPTIONS(description = 'Payment amount, USD. Negative or status=refunded for refunds.'),
  currency                  STRING             OPTIONS(description = 'ISO 4217 currency code.'),
  processor                 STRING             OPTIONS(description = 'Processor name: stripe, adyen, bank (for wires/ACH).'),
  processor_transaction_id  STRING             OPTIONS(description = 'Processor-side transaction ID for reconciliation.'),
  status                    STRING             OPTIONS(description = 'Status: succeeded, failed, refunded, pending.'),
  paid_at                   TIMESTAMP          OPTIONS(description = 'Timestamp the payment cleared. Partition key (by DATE).'),
  PRIMARY KEY (payment_id) NOT ENFORCED,
  FOREIGN KEY (invoice_id)  REFERENCES `acme_corp.invoices`(invoice_id)    NOT ENFORCED,
  FOREIGN KEY (customer_id) REFERENCES `acme_corp.customers`(customer_id)  NOT ENFORCED
)
PARTITION BY DATE(paid_at)
CLUSTER BY status
OPTIONS (description = 'Payment transactions against invoices. Partitioned by DATE(paid_at), clustered by status. May include refunds (status = refunded).');

-- =====================================================================
-- 5. SUPPORT
-- =====================================================================

-- support_tickets
CREATE OR REPLACE TABLE `acme_corp.support_tickets` (
  ticket_id           STRING    NOT NULL OPTIONS(description = 'Unique ticket identifier (format: TICK###). Primary key.'),
  customer_id         STRING             OPTIONS(description = 'FK to customers.customer_id. NULL for prospect or anonymous tickets.'),
  contact_id          STRING             OPTIONS(description = 'FK to customer_contacts.contact_id. The requester.'),
  subject             STRING             OPTIONS(description = 'Ticket subject line.'),
  description         STRING             OPTIONS(description = 'Initial problem description.'),
  priority            STRING             OPTIONS(description = 'Priority: low, normal, high, urgent.'),
  category            STRING             OPTIONS(description = 'Category: billing, technical, feature_request, bug.'),
  status              STRING             OPTIONS(description = 'Status: new, open, pending, solved, closed.'),
  assigned_to         STRING             OPTIONS(description = 'FK to employees.employee_id. Assigned support agent.'),
  created_at          TIMESTAMP          OPTIONS(description = 'Ticket creation time. Partition key (by DATE).'),
  first_response_at   TIMESTAMP          OPTIONS(description = 'First agent response. Drives first-response SLA.'),
  resolved_at         TIMESTAMP          OPTIONS(description = 'When the ticket was moved to solved/closed.'),
  csat_score          INT64              OPTIONS(description = 'Post-resolution CSAT 1-5. NULL if not surveyed or no response.'),
  PRIMARY KEY (ticket_id) NOT ENFORCED,
  FOREIGN KEY (customer_id) REFERENCES `acme_corp.customers`(customer_id)        NOT ENFORCED,
  FOREIGN KEY (contact_id)  REFERENCES `acme_corp.customer_contacts`(contact_id) NOT ENFORCED,
  FOREIGN KEY (assigned_to) REFERENCES `acme_corp.employees`(employee_id)        NOT ENFORCED
)
PARTITION BY DATE(created_at)
CLUSTER BY status, priority
OPTIONS (description = 'Customer support tickets. Partitioned by DATE(created_at), clustered by status, priority. SLA timestamps: first_response_at, resolved_at.');

-- ticket_comments
CREATE OR REPLACE TABLE `acme_corp.ticket_comments` (
  comment_id    STRING    NOT NULL OPTIONS(description = 'Unique comment identifier (format: TCOM###). Primary key.'),
  ticket_id     STRING    NOT NULL OPTIONS(description = 'FK to support_tickets.ticket_id.'),
  author_type   STRING             OPTIONS(description = 'Who authored the comment: customer, agent.'),
  author_id     STRING             OPTIONS(description = 'FK to customer_contacts.contact_id or employees.employee_id depending on author_type.'),
  body          STRING             OPTIONS(description = 'Comment body text.'),
  is_internal   BOOL               OPTIONS(description = 'TRUE for internal-only notes (not visible to customer).'),
  created_at    TIMESTAMP          OPTIONS(description = 'Comment timestamp. Partition key (by DATE).'),
  PRIMARY KEY (comment_id) NOT ENFORCED,
  FOREIGN KEY (ticket_id) REFERENCES `acme_corp.support_tickets`(ticket_id) NOT ENFORCED
)
PARTITION BY DATE(created_at)
OPTIONS (description = 'Chronological comments on support tickets. Partitioned by DATE(created_at). Includes internal-only notes (is_internal=TRUE).');

-- =====================================================================
-- 6. PROJECTS & VENDORS
-- =====================================================================

-- projects
CREATE OR REPLACE TABLE `acme_corp.projects` (
  project_id        STRING    NOT NULL OPTIONS(description = 'Unique project identifier (format: PROJ###). Primary key.'),
  name              STRING             OPTIONS(description = 'Project display name.'),
  description       STRING             OPTIONS(description = 'Free-text project description / charter summary.'),
  department_id     STRING             OPTIONS(description = 'FK to departments.department_id of the owning department.'),
  project_lead_id   STRING             OPTIONS(description = 'FK to employees.employee_id. The DRI.'),
  status            STRING             OPTIONS(description = 'Status: planned, active, on_hold, completed, cancelled.'),
  start_date        DATE               OPTIONS(description = 'Planned / actual start date.'),
  target_end_date   DATE               OPTIONS(description = 'Target completion date.'),
  actual_end_date   DATE               OPTIONS(description = 'Actual completion date. NULL while in flight.'),
  budget_usd        NUMERIC            OPTIONS(description = 'Approved budget in USD.'),
  spend_usd         NUMERIC            OPTIONS(description = 'Cumulative spend in USD.'),
  PRIMARY KEY (project_id) NOT ENFORCED,
  FOREIGN KEY (department_id)   REFERENCES `acme_corp.departments`(department_id) NOT ENFORCED,
  FOREIGN KEY (project_lead_id) REFERENCES `acme_corp.employees`(employee_id)     NOT ENFORCED
)
OPTIONS (description = 'Internal projects (cross-functional initiatives). Budget/spend tracks overrun. project_lead_id is the accountable DRI.');

-- project_assignments
CREATE OR REPLACE TABLE `acme_corp.project_assignments` (
  assignment_id    STRING   NOT NULL OPTIONS(description = 'Unique assignment identifier (format: PA###). Primary key.'),
  project_id       STRING   NOT NULL OPTIONS(description = 'FK to projects.project_id.'),
  employee_id      STRING   NOT NULL OPTIONS(description = 'FK to employees.employee_id.'),
  role             STRING            OPTIONS(description = 'Role on this project (e.g. "Tech Lead", "Designer", "Exec Sponsor").'),
  allocation_pct   NUMERIC           OPTIONS(description = 'Percentage of time allocated (0-100).'),
  start_date       DATE              OPTIONS(description = 'Assignment start date.'),
  end_date         DATE              OPTIONS(description = 'Assignment end date. NULL for ongoing.'),
  PRIMARY KEY (assignment_id) NOT ENFORCED,
  FOREIGN KEY (project_id)  REFERENCES `acme_corp.projects`(project_id)   NOT ENFORCED,
  FOREIGN KEY (employee_id) REFERENCES `acme_corp.employees`(employee_id) NOT ENFORCED
)
OPTIONS (description = 'Employee allocations to projects. Multiple rows per employee / project possible over time.');

-- vendors
CREATE OR REPLACE TABLE `acme_corp.vendors` (
  vendor_id        STRING   NOT NULL OPTIONS(description = 'Unique vendor identifier (format: VEN###). Primary key.'),
  name             STRING            OPTIONS(description = 'Vendor legal name.'),
  category         STRING            OPTIONS(description = 'Category: saas, hardware, consulting, facilities.'),
  contact_email    STRING            OPTIONS(description = 'Primary vendor contact email.'),
  contact_phone    STRING            OPTIONS(description = 'Primary vendor contact phone (E.164).'),
  country          STRING            OPTIONS(description = 'ISO 3166-1 alpha-2 country of registration.'),
  onboarded_date   DATE              OPTIONS(description = 'Date vendor was approved and onboarded.'),
  status           STRING            OPTIONS(description = 'Status: active, inactive, pending_review.'),
  risk_rating      STRING            OPTIONS(description = 'Security risk rating: low, medium, high. High-risk vendors get annual re-review.'),
  PRIMARY KEY (vendor_id) NOT ENFORCED
)
OPTIONS (description = 'Third-party vendors / suppliers. Risk rating drives security review cadence.');

-- vendor_contracts
CREATE OR REPLACE TABLE `acme_corp.vendor_contracts` (
  contract_id         STRING    NOT NULL OPTIONS(description = 'Unique contract identifier (format: VC###). Primary key.'),
  vendor_id           STRING    NOT NULL OPTIONS(description = 'FK to vendors.vendor_id.'),
  owner_employee_id   STRING             OPTIONS(description = 'FK to employees.employee_id. Internal contract owner.'),
  start_date          DATE               OPTIONS(description = 'Contract start date.'),
  end_date            DATE               OPTIONS(description = 'Contract end date.'),
  annual_spend_usd    NUMERIC            OPTIONS(description = 'Committed / expected annual spend in USD.'),
  currency            STRING             OPTIONS(description = 'ISO 4217 currency code of the contract.'),
  auto_renew          BOOL               OPTIONS(description = 'TRUE if the contract auto-renews absent cancellation notice.'),
  status              STRING             OPTIONS(description = 'Contract status: active, expired, terminated.'),
  signed_at           TIMESTAMP          OPTIONS(description = 'When the contract was fully executed.'),
  PRIMARY KEY (contract_id) NOT ENFORCED,
  FOREIGN KEY (vendor_id)         REFERENCES `acme_corp.vendors`(vendor_id)      NOT ENFORCED,
  FOREIGN KEY (owner_employee_id) REFERENCES `acme_corp.employees`(employee_id)  NOT ENFORCED
)
OPTIONS (description = 'Contracts with vendors. Tracks annual spend and auto-renewal for procurement / FP&A.');

-- =====================================================================
-- 7. MARKETING / WEB ANALYTICS
-- =====================================================================

-- web_events
CREATE OR REPLACE TABLE `acme_corp.web_events` (
  event_id       STRING    NOT NULL OPTIONS(description = 'Unique event identifier (format: EV###). Primary key.'),
  session_id     STRING             OPTIONS(description = 'Session identifier grouping events from one browsing session.'),
  visitor_id     STRING             OPTIONS(description = 'Persistent anonymous visitor identifier (cookie-based).'),
  customer_id    STRING             OPTIONS(description = 'FK to customers.customer_id. Populated post-identification (e.g. logged-in user).'),
  event_type     STRING             OPTIONS(description = 'Event type: page_view, click, form_submit, signup.'),
  page_url       STRING             OPTIONS(description = 'Full URL where the event occurred.'),
  referrer       STRING             OPTIONS(description = 'HTTP referrer URL, if any.'),
  utm_source     STRING             OPTIONS(description = 'UTM source parameter.'),
  utm_medium     STRING             OPTIONS(description = 'UTM medium parameter.'),
  utm_campaign   STRING             OPTIONS(description = 'UTM campaign parameter. Often matches campaigns.campaign_id but not enforced.'),
  device_type    STRING             OPTIONS(description = 'Device type: desktop, mobile, tablet.'),
  country        STRING             OPTIONS(description = 'ISO 3166-1 alpha-2 country derived from IP.'),
  event_at       TIMESTAMP          OPTIONS(description = 'When the event fired. Partition key (by DATE).'),
  PRIMARY KEY (event_id) NOT ENFORCED,
  FOREIGN KEY (customer_id) REFERENCES `acme_corp.customers`(customer_id) NOT ENFORCED
)
PARTITION BY DATE(event_at)
CLUSTER BY event_type, utm_source
OPTIONS (description = 'Web analytics events from acme.example. Partitioned by DATE(event_at), clustered by event_type, utm_source. High-volume; prefer partition-pruned queries.');


-- =====================================================================
-- ACME Corp — seed data (10+ rows per table, 31 tables)
-- Run AFTER acme_corp_bigquery_schema.sql
-- Insert order respects dependencies even though FKs are NOT ENFORCED.
-- =====================================================================

-- =====================================================================
-- 1. OFFICES
-- =====================================================================
INSERT INTO `acme_corp.offices`
(office_id, name, country, city, address, timezone, headcount_capacity, opened_date, is_hq, created_at) VALUES
('OFF001','San Francisco HQ','US','San Francisco','525 Market St, Suite 2000','America/Los_Angeles',450,DATE '2015-03-01',TRUE, TIMESTAMP '2015-03-01 09:00:00 UTC'),
('OFF002','New York','US','New York','1 World Trade Center, Fl 45','America/New_York',220,DATE '2017-06-15',FALSE, TIMESTAMP '2017-06-15 09:00:00 UTC'),
('OFF003','Austin','US','Austin','500 W 2nd St','America/Chicago',180,DATE '2019-02-20',FALSE, TIMESTAMP '2019-02-20 09:00:00 UTC'),
('OFF004','London','GB','London','20 Farringdon Rd','Europe/London',160,DATE '2018-09-10',FALSE, TIMESTAMP '2018-09-10 09:00:00 UTC'),
('OFF005','Dublin','IE','Dublin','Grand Canal Dock, 5 Hanover Quay','Europe/Dublin',120,DATE '2020-01-15',FALSE, TIMESTAMP '2020-01-15 09:00:00 UTC'),
('OFF006','Berlin','DE','Berlin','Friedrichstraße 68','Europe/Berlin',90,DATE '2021-05-01',FALSE, TIMESTAMP '2021-05-01 09:00:00 UTC'),
('OFF007','Tokyo','JP','Tokyo','Shibuya Scramble Square, Fl 30','Asia/Tokyo',80,DATE '2022-04-01',FALSE, TIMESTAMP '2022-04-01 09:00:00 UTC'),
('OFF008','Sydney','AU','Sydney','1 Martin Place','Australia/Sydney',60,DATE '2022-11-10',FALSE, TIMESTAMP '2022-11-10 09:00:00 UTC'),
('OFF009','Toronto','CA','Toronto','100 King St W','America/Toronto',100,DATE '2023-03-01',FALSE, TIMESTAMP '2023-03-01 09:00:00 UTC'),
('OFF010','Singapore','SG','Singapore','1 Raffles Place','Asia/Singapore',70,DATE '2024-02-14',FALSE, TIMESTAMP '2024-02-14 09:00:00 UTC');

-- =====================================================================
-- 2. DEPARTMENTS (parent refs self; head_employee_id filled via UPDATE later)
-- =====================================================================
INSERT INTO `acme_corp.departments`
(department_id, name, cost_center, parent_department_id, head_employee_id, budget_annual_usd, created_at) VALUES
('DEPT001','Engineering','CC-1000',NULL,NULL, 28000000, TIMESTAMP '2015-03-01 09:00:00 UTC'),
('DEPT002','Product','CC-1100',NULL,NULL,  6500000, TIMESTAMP '2015-03-01 09:00:00 UTC'),
('DEPT003','Sales','CC-2000',NULL,NULL,   14000000, TIMESTAMP '2015-03-01 09:00:00 UTC'),
('DEPT004','Marketing','CC-2100',NULL,NULL, 5200000, TIMESTAMP '2015-03-01 09:00:00 UTC'),
('DEPT005','Customer Success','CC-2200','DEPT003',NULL, 3800000, TIMESTAMP '2016-01-10 09:00:00 UTC'),
('DEPT006','Support','CC-2300','DEPT005',NULL,        2100000, TIMESTAMP '2016-06-01 09:00:00 UTC'),
('DEPT007','Finance','CC-3000',NULL,NULL,             1800000, TIMESTAMP '2015-03-01 09:00:00 UTC'),
('DEPT008','People Ops','CC-3100',NULL,NULL,          1500000, TIMESTAMP '2015-03-01 09:00:00 UTC'),
('DEPT009','Legal','CC-3200',NULL,NULL,                900000, TIMESTAMP '2016-02-01 09:00:00 UTC'),
('DEPT010','IT','CC-3300',NULL,NULL,                  1200000, TIMESTAMP '2017-01-15 09:00:00 UTC');

-- =====================================================================
-- 3. JOB TITLES
-- =====================================================================
INSERT INTO `acme_corp.job_titles`
(job_title_id, title, level, job_family, min_salary, max_salary, currency) VALUES
('JT001','Software Engineer','IC3','engineering',130000,165000,'USD'),
('JT002','Senior Software Engineer','IC4','engineering',165000,205000,'USD'),
('JT003','Staff Software Engineer','IC5','engineering',205000,260000,'USD'),
('JT004','Engineering Manager','M3','engineering',210000,265000,'USD'),
('JT005','Director of Engineering','M4','engineering',260000,330000,'USD'),
('JT006','Account Executive','IC3','sales',110000,150000,'USD'),
('JT007','Sales Manager','M3','sales',180000,230000,'USD'),
('JT008','Product Manager','IC4','product',170000,215000,'USD'),
('JT009','Product Designer','IC3','product',140000,180000,'USD'),
('JT010','Customer Success Manager','IC3','customer_success',105000,140000,'USD');

-- =====================================================================
-- 4. EMPLOYEES
-- =====================================================================
INSERT INTO `acme_corp.employees`
(employee_id, first_name, last_name, email, phone, hire_date, termination_date, employment_status, employment_type,
 manager_id, department_id, team_id, job_title_id, office_id, date_of_birth, gender, country, emergency_contact, skills, created_at, updated_at) VALUES
('EMP001','Sarah','Chen','sarah.chen@acme.com','+1-415-555-0101',DATE '2016-04-11',NULL,'active','full_time',
  NULL,'DEPT001',NULL,'JT005','OFF001',DATE '1983-07-22','F','US',
  STRUCT('David Chen' AS name,'spouse' AS relation,'+1-415-555-9101' AS phone),
  ['python','golang','kubernetes','leadership'],
  TIMESTAMP '2016-04-11 09:00:00 UTC', TIMESTAMP '2025-10-01 09:00:00 UTC'),
('EMP002','Marcus','Johnson','marcus.johnson@acme.com','+1-415-555-0102',DATE '2017-08-21',NULL,'active','full_time',
  'EMP001','DEPT001',NULL,'JT004','OFF001',DATE '1985-11-02','M','US',
  STRUCT('Linda Johnson' AS name,'parent' AS relation,'+1-415-555-9102' AS phone),
  ['java','spring','aws','mentoring'],
  TIMESTAMP '2017-08-21 09:00:00 UTC', TIMESTAMP '2025-09-12 09:00:00 UTC'),
('EMP003','Priya','Patel','priya.patel@acme.com','+1-415-555-0103',DATE '2019-03-04',NULL,'active','full_time',
  'EMP002','DEPT001',NULL,'JT003','OFF001',DATE '1989-05-14','F','US',
  STRUCT('Raj Patel' AS name,'sibling' AS relation,'+1-415-555-9103' AS phone),
  ['python','neo4j','graph_algorithms','sql'],
  TIMESTAMP '2019-03-04 09:00:00 UTC', TIMESTAMP '2025-08-20 09:00:00 UTC'),
('EMP004','Tomaz','Bratanic','tomaz.bratanic@acme.com','+386-1-555-0104',DATE '2020-07-15',NULL,'active','full_time',
  'EMP002','DEPT001',NULL,'JT002','OFF006',DATE '1990-02-18','M','SI',
  STRUCT('Ana Bratanic' AS name,'spouse' AS relation,'+386-1-555-9104' AS phone),
  ['python','neo4j','cypher','llm','graphrag'],
  TIMESTAMP '2020-07-15 09:00:00 UTC', TIMESTAMP '2026-02-01 09:00:00 UTC'),
('EMP005','Yuki','Tanaka','yuki.tanaka@acme.com','+81-3-5555-0105',DATE '2022-05-02',NULL,'active','full_time',
  'EMP002','DEPT001',NULL,'JT001','OFF007',DATE '1994-09-30','F','JP',
  STRUCT('Hiro Tanaka' AS name,'parent' AS relation,'+81-3-5555-9105' AS phone),
  ['typescript','react','graphql'],
  TIMESTAMP '2022-05-02 09:00:00 UTC', TIMESTAMP '2026-01-10 09:00:00 UTC'),
('EMP006','Aisha','Okafor','aisha.okafor@acme.com','+1-212-555-0106',DATE '2018-11-30',NULL,'active','full_time',
  NULL,'DEPT003',NULL,'JT007','OFF002',DATE '1984-03-11','F','US',
  STRUCT('Chidi Okafor' AS name,'spouse' AS relation,'+1-212-555-9106' AS phone),
  ['enterprise_sales','negotiation','salesforce'],
  TIMESTAMP '2018-11-30 09:00:00 UTC', TIMESTAMP '2025-11-15 09:00:00 UTC'),
('EMP007','James','O\'Brien','james.obrien@acme.com','+353-1-555-0107',DATE '2020-01-20',NULL,'active','full_time',
  'EMP006','DEPT003',NULL,'JT006','OFF005',DATE '1991-06-25','M','IE',
  STRUCT('Mary O\'Brien' AS name,'spouse' AS relation,'+353-1-555-9107' AS phone),
  ['saas_sales','outbound','emea'],
  TIMESTAMP '2020-01-20 09:00:00 UTC', TIMESTAMP '2025-12-05 09:00:00 UTC'),
('EMP008','Elena','Rodríguez','elena.rodriguez@acme.com','+44-20-5555-0108',DATE '2021-09-06',NULL,'active','full_time',
  'EMP006','DEPT003',NULL,'JT006','OFF004',DATE '1992-12-01','F','GB',
  STRUCT('Carlos Rodríguez' AS name,'parent' AS relation,'+44-20-5555-9108' AS phone),
  ['mid_market_sales','demo_delivery','discovery'],
  TIMESTAMP '2021-09-06 09:00:00 UTC', TIMESTAMP '2026-01-20 09:00:00 UTC'),
('EMP009','Michael','Weber','michael.weber@acme.com','+1-512-555-0109',DATE '2019-06-10',NULL,'active','full_time',
  NULL,'DEPT002',NULL,'JT008','OFF003',DATE '1987-08-09','M','US',
  STRUCT('Rachel Weber' AS name,'spouse' AS relation,'+1-512-555-9109' AS phone),
  ['product_strategy','roadmapping','figma'],
  TIMESTAMP '2019-06-10 09:00:00 UTC', TIMESTAMP '2025-10-30 09:00:00 UTC'),
('EMP010','Zara','Ahmed','zara.ahmed@acme.com','+1-416-555-0110',DATE '2021-02-08',NULL,'active','full_time',
  'EMP009','DEPT002',NULL,'JT009','OFF009',DATE '1993-04-17','F','CA',
  STRUCT('Omar Ahmed' AS name,'sibling' AS relation,'+1-416-555-9110' AS phone),
  ['ux_research','figma','accessibility'],
  TIMESTAMP '2021-02-08 09:00:00 UTC', TIMESTAMP '2025-09-01 09:00:00 UTC'),
('EMP011','Chen','Liu','chen.liu@acme.com','+65-6555-0111',DATE '2023-04-18',NULL,'active','full_time',
  NULL,'DEPT005',NULL,'JT010','OFF010',DATE '1990-10-05','M','SG',
  STRUCT('Mei Liu' AS name,'spouse' AS relation,'+65-6555-9111' AS phone),
  ['customer_success','apac','onboarding'],
  TIMESTAMP '2023-04-18 09:00:00 UTC', TIMESTAMP '2025-12-20 09:00:00 UTC'),
('EMP012','Oliver','Schmidt','oliver.schmidt@acme.com','+49-30-555-0112',DATE '2022-10-03',DATE '2025-06-30','terminated','full_time',
  'EMP002','DEPT001',NULL,'JT001','OFF006',DATE '1995-01-22','M','DE',
  STRUCT('Klara Schmidt' AS name,'parent' AS relation,'+49-30-555-9112' AS phone),
  ['rust','systems_programming'],
  TIMESTAMP '2022-10-03 09:00:00 UTC', TIMESTAMP '2025-06-30 17:00:00 UTC');

-- Backfill department heads now that employees exist
UPDATE `acme_corp.departments` SET head_employee_id = 'EMP001' WHERE department_id = 'DEPT001';
UPDATE `acme_corp.departments` SET head_employee_id = 'EMP009' WHERE department_id = 'DEPT002';
UPDATE `acme_corp.departments` SET head_employee_id = 'EMP006' WHERE department_id = 'DEPT003';
UPDATE `acme_corp.departments` SET head_employee_id = 'EMP011' WHERE department_id = 'DEPT005';

-- =====================================================================
-- 5. TEAMS (now assign team_id back to employees afterwards)
-- =====================================================================
INSERT INTO `acme_corp.teams`
(team_id, name, department_id, lead_employee_id, slack_channel, formed_date, is_active) VALUES
('TEAM001','Platform','DEPT001','EMP002','#team-platform',DATE '2017-09-01',TRUE),
('TEAM002','Data & Graph','DEPT001','EMP003','#team-data-graph',DATE '2019-04-01',TRUE),
('TEAM003','Frontend','DEPT001','EMP005','#team-frontend',DATE '2018-03-15',TRUE),
('TEAM004','Backend','DEPT001','EMP004','#team-backend',DATE '2020-09-01',TRUE),
('TEAM005','SMB Sales','DEPT003','EMP007','#sales-smb',DATE '2020-02-01',TRUE),
('TEAM006','Enterprise Sales','DEPT003','EMP006','#sales-enterprise',DATE '2019-01-10',TRUE),
('TEAM007','Demand Gen','DEPT004',NULL,'#marketing-demand-gen',DATE '2018-06-01',TRUE),
('TEAM008','Support L1','DEPT006',NULL,'#support-l1',DATE '2017-02-01',TRUE),
('TEAM009','Support L2','DEPT006',NULL,'#support-l2',DATE '2018-10-01',TRUE),
('TEAM010','FP&A','DEPT007',NULL,'#fpa',DATE '2016-01-10',TRUE);

UPDATE `acme_corp.employees` SET team_id = 'TEAM001' WHERE employee_id IN ('EMP002');
UPDATE `acme_corp.employees` SET team_id = 'TEAM002' WHERE employee_id IN ('EMP003');
UPDATE `acme_corp.employees` SET team_id = 'TEAM004' WHERE employee_id IN ('EMP004','EMP012');
UPDATE `acme_corp.employees` SET team_id = 'TEAM003' WHERE employee_id IN ('EMP005');
UPDATE `acme_corp.employees` SET team_id = 'TEAM006' WHERE employee_id IN ('EMP006');
UPDATE `acme_corp.employees` SET team_id = 'TEAM005' WHERE employee_id IN ('EMP007','EMP008');

-- =====================================================================
-- 6. EMPLOYEE ROLE HISTORY
-- =====================================================================
INSERT INTO `acme_corp.employee_role_history`
(role_history_id, employee_id, job_title_id, department_id, team_id, manager_id, start_date, end_date, change_reason) VALUES
('RH001','EMP001','JT004','DEPT001',NULL,NULL,       DATE '2016-04-11',DATE '2019-06-30','new_hire'),
('RH002','EMP001','JT005','DEPT001',NULL,NULL,       DATE '2019-07-01',NULL,              'promotion'),
('RH003','EMP002','JT002','DEPT001','TEAM001','EMP001',DATE '2017-08-21',DATE '2020-12-31','new_hire'),
('RH004','EMP002','JT004','DEPT001','TEAM001','EMP001',DATE '2021-01-01',NULL,              'promotion'),
('RH005','EMP003','JT002','DEPT001','TEAM002','EMP002',DATE '2019-03-04',DATE '2023-03-31','new_hire'),
('RH006','EMP003','JT003','DEPT001','TEAM002','EMP002',DATE '2023-04-01',NULL,              'promotion'),
('RH007','EMP004','JT001','DEPT001','TEAM004','EMP002',DATE '2020-07-15',DATE '2023-06-30','new_hire'),
('RH008','EMP004','JT002','DEPT001','TEAM004','EMP002',DATE '2023-07-01',NULL,              'promotion'),
('RH009','EMP007','JT006','DEPT003','TEAM005','EMP006',DATE '2020-01-20',NULL,              'new_hire'),
('RH010','EMP012','JT001','DEPT001','TEAM004','EMP002',DATE '2022-10-03',DATE '2025-06-30','termination');

-- =====================================================================
-- 7. COMPENSATION
-- =====================================================================
INSERT INTO `acme_corp.compensation`
(compensation_id, employee_id, effective_date, base_salary, bonus_target_pct, equity_grant_usd, currency, change_type, approved_by) VALUES
('COMP001','EMP001',DATE '2016-04-11',195000,15,250000,'USD','new_hire','EMP006'),
('COMP002','EMP001',DATE '2024-04-01',310000,25,500000,'USD','merit','EMP001'),
('COMP003','EMP002',DATE '2017-08-21',165000,12,150000,'USD','new_hire','EMP001'),
('COMP004','EMP002',DATE '2024-04-01',245000,20,300000,'USD','merit','EMP001'),
('COMP005','EMP003',DATE '2019-03-04',170000,10,120000,'USD','new_hire','EMP002'),
('COMP006','EMP003',DATE '2023-04-01',230000,15,200000,'USD','promotion','EMP002'),
('COMP007','EMP004',DATE '2020-07-15',135000,10,80000,'USD','new_hire','EMP002'),
('COMP008','EMP004',DATE '2023-07-01',180000,12,150000,'USD','promotion','EMP002'),
('COMP009','EMP006',DATE '2018-11-30',180000,30,200000,'USD','new_hire','EMP001'),
('COMP010','EMP007',DATE '2020-01-20',115000,40,60000,'USD','new_hire','EMP006');

-- =====================================================================
-- 8. PERFORMANCE REVIEWS
-- =====================================================================
INSERT INTO `acme_corp.performance_reviews`
(review_id, employee_id, reviewer_id, review_period, overall_rating, numeric_score, strengths, areas_for_improvement, submitted_at) VALUES
('REV001','EMP002','EMP001','2024-H2','exceeds',4.5,'Strong technical leadership; mentored 3 juniors','Could delegate more strategic work', TIMESTAMP '2025-01-15 17:00:00 UTC'),
('REV002','EMP003','EMP002','2024-H2','exceeds',4.6,'Deep graph expertise; drove Neocarta architecture','More cross-team communication', TIMESTAMP '2025-01-16 17:00:00 UTC'),
('REV003','EMP004','EMP002','2024-H2','exceeds',4.7,'Shipped GraphRAG chapter; blog posts drove inbound','Take more ownership of roadmap', TIMESTAMP '2025-01-17 17:00:00 UTC'),
('REV004','EMP005','EMP002','2024-H2','meets',3.8,'Solid frontend contributions','Improve code review turnaround', TIMESTAMP '2025-01-18 17:00:00 UTC'),
('REV005','EMP007','EMP006','2024-H2','exceeds',4.4,'Closed 112% of quota','Forecast accuracy', TIMESTAMP '2025-01-20 17:00:00 UTC'),
('REV006','EMP008','EMP006','2024-H2','meets',3.6,'Strong discovery calls','Demo delivery confidence', TIMESTAMP '2025-01-20 17:00:00 UTC'),
('REV007','EMP009','EMP001','2024-H2','exceeds',4.5,'Great roadmap clarity','Stakeholder management in EMEA', TIMESTAMP '2025-01-22 17:00:00 UTC'),
('REV008','EMP010','EMP009','2024-H2','meets',3.9,'Thoughtful UX research','Ship more design systems work', TIMESTAMP '2025-01-22 17:00:00 UTC'),
('REV009','EMP011','EMP006','2024-H2','meets',3.7,'Fast APAC onboarding ramp','Deepen product knowledge', TIMESTAMP '2025-01-25 17:00:00 UTC'),
('REV010','EMP012','EMP002','2024-H2','below',2.4,'Good first-year progress','Code quality; communication', TIMESTAMP '2025-01-28 17:00:00 UTC');

-- =====================================================================
-- 9. TIME OFF REQUESTS
-- =====================================================================
INSERT INTO `acme_corp.time_off_requests`
(request_id, employee_id, request_type, start_date, end_date, total_days, status, approver_id, requested_at) VALUES
('TOR001','EMP002','vacation',DATE '2025-07-21',DATE '2025-08-01',10,'approved','EMP001', TIMESTAMP '2025-05-10 10:00:00 UTC'),
('TOR002','EMP003','vacation',DATE '2025-12-22',DATE '2026-01-02',8,'approved','EMP002', TIMESTAMP '2025-10-15 14:30:00 UTC'),
('TOR003','EMP004','vacation',DATE '2026-05-12',DATE '2026-05-23',10,'approved','EMP002', TIMESTAMP '2026-02-20 09:15:00 UTC'),
('TOR004','EMP005','sick',    DATE '2026-01-05',DATE '2026-01-07', 3,'approved','EMP002', TIMESTAMP '2026-01-04 07:30:00 UTC'),
('TOR005','EMP007','vacation',DATE '2025-08-11',DATE '2025-08-22',10,'approved','EMP006', TIMESTAMP '2025-06-01 11:00:00 UTC'),
('TOR006','EMP008','parental',DATE '2025-09-01',DATE '2025-12-01',65,'approved','EMP006', TIMESTAMP '2025-05-15 09:00:00 UTC'),
('TOR007','EMP009','vacation',DATE '2026-03-23',DATE '2026-03-30', 6,'approved','EMP001', TIMESTAMP '2026-01-10 16:00:00 UTC'),
('TOR008','EMP010','vacation',DATE '2026-06-01',DATE '2026-06-12',10,'pending','EMP009',  TIMESTAMP '2026-04-01 13:00:00 UTC'),
('TOR009','EMP011','bereavement',DATE '2025-11-03',DATE '2025-11-07',5,'approved','EMP006', TIMESTAMP '2025-11-02 08:00:00 UTC'),
('TOR010','EMP012','sick',    DATE '2025-05-20',DATE '2025-05-22', 3,'approved','EMP002', TIMESTAMP '2025-05-19 22:00:00 UTC');

-- =====================================================================
-- 10. TRAINING COURSES
-- =====================================================================
INSERT INTO `acme_corp.training_courses`
(course_id, title, provider, category, duration_hours, is_mandatory, created_at) VALUES
('CRS001','Security Awareness 101','SecureEdu','compliance',2, TRUE, TIMESTAMP '2020-01-15 09:00:00 UTC'),
('CRS002','GDPR for Engineers','DataPrivacy Inc','compliance',3, TRUE, TIMESTAMP '2020-05-20 09:00:00 UTC'),
('CRS003','Advanced Cypher','Neo4j Academy','engineering',8, FALSE, TIMESTAMP '2021-03-10 09:00:00 UTC'),
('CRS004','Graph Data Science','Neo4j Academy','engineering',12,FALSE, TIMESTAMP '2022-02-14 09:00:00 UTC'),
('CRS005','GraphRAG Fundamentals','Internal','engineering',6, FALSE, TIMESTAMP '2024-06-01 09:00:00 UTC'),
('CRS006','Handling Difficult Conversations','HBR Learning','leadership',4, FALSE, TIMESTAMP '2021-09-01 09:00:00 UTC'),
('CRS007','MEDDIC for AEs','Winning by Design','sales',10, FALSE, TIMESTAMP '2022-11-05 09:00:00 UTC'),
('CRS008','Anti-Harassment Training','EverFi','compliance',1, TRUE, TIMESTAMP '2020-01-15 09:00:00 UTC'),
('CRS009','SQL for Analysts','DataCamp','analytics',8, FALSE, TIMESTAMP '2023-04-10 09:00:00 UTC'),
('CRS010','Effective Technical Writing','Internal','engineering',3, FALSE, TIMESTAMP '2023-10-01 09:00:00 UTC');

-- =====================================================================
-- 11. EMPLOYEE TRAINING
-- =====================================================================
INSERT INTO `acme_corp.employee_training`
(enrollment_id, employee_id, course_id, enrolled_at, completed_at, completion_status, score) VALUES
('ENR001','EMP002','CRS001', TIMESTAMP '2024-01-10 09:00:00 UTC', TIMESTAMP '2024-01-10 11:00:00 UTC','completed',95),
('ENR002','EMP003','CRS003', TIMESTAMP '2024-02-05 09:00:00 UTC', TIMESTAMP '2024-02-19 16:00:00 UTC','completed',98),
('ENR003','EMP004','CRS003', TIMESTAMP '2024-02-05 09:00:00 UTC', TIMESTAMP '2024-02-15 14:00:00 UTC','completed',96),
('ENR004','EMP004','CRS005', TIMESTAMP '2024-06-05 09:00:00 UTC', TIMESTAMP '2024-06-10 12:00:00 UTC','completed',99),
('ENR005','EMP005','CRS001', TIMESTAMP '2024-01-10 09:00:00 UTC', TIMESTAMP '2024-01-10 11:30:00 UTC','completed',88),
('ENR006','EMP007','CRS007', TIMESTAMP '2024-03-12 09:00:00 UTC', TIMESTAMP '2024-03-22 17:00:00 UTC','completed',91),
('ENR007','EMP008','CRS007', TIMESTAMP '2024-03-12 09:00:00 UTC',NULL,                                'in_progress',NULL),
('ENR008','EMP010','CRS009', TIMESTAMP '2024-05-20 09:00:00 UTC', TIMESTAMP '2024-06-01 15:00:00 UTC','completed',87),
('ENR009','EMP011','CRS002', TIMESTAMP '2024-04-18 09:00:00 UTC', TIMESTAMP '2024-04-18 12:30:00 UTC','completed',92),
('ENR010','EMP012','CRS001', TIMESTAMP '2024-01-12 09:00:00 UTC',NULL,                                'abandoned',NULL);

-- =====================================================================
-- 12. CUSTOMERS
-- =====================================================================
INSERT INTO `acme_corp.customers`
(customer_id, company_name, industry, annual_revenue_usd, employee_count, website, country, segment,
 acquired_date, account_owner_id, status, lifetime_value_usd, health_score, tags, created_at) VALUES
('CUST001','Globex Financial','financial_services', 2400000000, 8500,'globex-financial.com','US','enterprise',
  DATE '2019-10-15','EMP006','active', 4200000, 87,['strategic','expansion_candidate'], TIMESTAMP '2019-10-15 09:00:00 UTC'),
('CUST002','Initech Systems','technology',            180000000,  650,'initech.com','US','mid_market',
  DATE '2021-03-22','EMP007','active',  620000, 72,['reference_customer'], TIMESTAMP '2021-03-22 09:00:00 UTC'),
('CUST003','Soylent Retail','retail',                 950000000, 3200,'soylent-retail.com','GB','enterprise',
  DATE '2020-06-10','EMP008','active', 1800000, 68,['at_risk'], TIMESTAMP '2020-06-10 09:00:00 UTC'),
('CUST004','Acme Widgets Co','manufacturing',          45000000,  280,'acme-widgets.example','DE','mid_market',
  DATE '2022-11-02','EMP007','active',  340000, 81,[], TIMESTAMP '2022-11-02 09:00:00 UTC'),
('CUST005','Stark Industries','manufacturing',       5200000000,14500,'stark.example','US','enterprise',
  DATE '2018-04-30','EMP006','active', 6100000, 91,['strategic','advocate'], TIMESTAMP '2018-04-30 09:00:00 UTC'),
('CUST006','Hooli Labs','technology',                 720000000, 1900,'hooli.example','US','mid_market',
  DATE '2023-01-17','EMP007','active',  280000, 64,['low_engagement'], TIMESTAMP '2023-01-17 09:00:00 UTC'),
('CUST007','Umbrella Biotech','healthcare',           430000000, 1100,'umbrella-bio.example','CH','mid_market',
  DATE '2022-05-08','EMP008','churned', 520000, 30,['churned','recompete'], TIMESTAMP '2022-05-08 09:00:00 UTC'),
('CUST008','Tyrell Data','data_analytics',             80000000,  350,'tyrell-data.example','JP','mid_market',
  DATE '2023-09-14','EMP007','active',  190000, 78,[], TIMESTAMP '2023-09-14 09:00:00 UTC'),
('CUST009','Massive Dynamic','technology',          12000000000,42000,'massive-dynamic.example','US','enterprise',
  DATE '2017-02-01','EMP006','active', 9800000, 95,['strategic','advocate','case_study'], TIMESTAMP '2017-02-01 09:00:00 UTC'),
('CUST010','Prometheus AI','technology',               25000000,   90,'prometheus-ai.example','SG','smb',
  DATE '2024-08-05','EMP011','prospect', 0, 55,['pilot'], TIMESTAMP '2024-08-05 09:00:00 UTC');

-- =====================================================================
-- 13. CUSTOMER CONTACTS
-- =====================================================================
INSERT INTO `acme_corp.customer_contacts`
(contact_id, customer_id, first_name, last_name, email, phone, title, is_primary, is_decision_maker, created_at) VALUES
('CONTACT001','CUST001','Helena','Cruz','hcruz@globex-financial.com','+1-212-555-1001','VP Data Platform',TRUE, TRUE,  TIMESTAMP '2019-10-15 09:00:00 UTC'),
('CONTACT002','CUST001','Omar','Hassan','ohassan@globex-financial.com','+1-212-555-1002','Director of Engineering',FALSE,FALSE,TIMESTAMP '2019-11-10 09:00:00 UTC'),
('CONTACT003','CUST002','Bill','Lumbergh','blumbergh@initech.com','+1-512-555-1003','CTO',TRUE, TRUE, TIMESTAMP '2021-03-22 09:00:00 UTC'),
('CONTACT004','CUST003','Harriet','Knight','hknight@soylent-retail.com','+44-20-5555-1004','Head of Data',TRUE, TRUE, TIMESTAMP '2020-06-10 09:00:00 UTC'),
('CONTACT005','CUST004','Dieter','Müller','dmueller@acme-widgets.example','+49-30-555-1005','IT Director',TRUE, TRUE, TIMESTAMP '2022-11-02 09:00:00 UTC'),
('CONTACT006','CUST005','Pepper','Potts','ppotts@stark.example','+1-213-555-1006','VP Engineering',TRUE, TRUE, TIMESTAMP '2018-04-30 09:00:00 UTC'),
('CONTACT007','CUST006','Richard','Hendricks','rhendricks@hooli.example','+1-415-555-1007','Principal Engineer',TRUE, FALSE, TIMESTAMP '2023-01-17 09:00:00 UTC'),
('CONTACT008','CUST007','Albert','Wesker','awesker@umbrella-bio.example','+41-22-555-1008','Head of Informatics',TRUE, TRUE, TIMESTAMP '2022-05-08 09:00:00 UTC'),
('CONTACT009','CUST008','Rachael','Deckard','rdeckard@tyrell-data.example','+81-3-5555-1009','CTO',TRUE, TRUE, TIMESTAMP '2023-09-14 09:00:00 UTC'),
('CONTACT010','CUST009','Nina','Sharp','nsharp@massive-dynamic.example','+1-617-555-1010','SVP Platform',TRUE, TRUE, TIMESTAMP '2017-02-01 09:00:00 UTC'),
('CONTACT011','CUST010','Elizabeth','Shaw','eshaw@prometheus-ai.example','+65-6555-1011','Co-founder & CTO',TRUE, TRUE, TIMESTAMP '2024-08-05 09:00:00 UTC');

-- =====================================================================
-- 14. CUSTOMER ADDRESSES
-- =====================================================================
INSERT INTO `acme_corp.customer_addresses`
(address_id, customer_id, address_type, line1, line2, city, region, postal_code, country, is_primary) VALUES
('ADDR001','CUST001','hq',       '200 Park Ave', 'Fl 40',              'New York','NY','10166','US',TRUE),
('ADDR002','CUST001','billing',  '200 Park Ave', 'AP Dept, Fl 38',      'New York','NY','10166','US',FALSE),
('ADDR003','CUST002','hq',       '1500 Congress Ave',NULL,              'Austin','TX','78701','US',TRUE),
('ADDR004','CUST003','hq',       '10 Paternoster Sq',NULL,              'London','England','EC4M 7LS','GB',TRUE),
('ADDR005','CUST004','hq',       'Unter den Linden 10',NULL,            'Berlin','Berlin','10117','DE',TRUE),
('ADDR006','CUST005','hq',       '10880 Malibu Point',NULL,             'Malibu','CA','90265','US',TRUE),
('ADDR007','CUST006','hq',       '1401 N Shoreline Blvd',NULL,          'Mountain View','CA','94043','US',TRUE),
('ADDR008','CUST007','hq',       'Raccoon Plaza 1',NULL,                'Geneva','GE','1204','CH',TRUE),
('ADDR009','CUST008','hq',       '2-4-1 Nishi-Shinjuku','Tower Fl 50',  'Tokyo','Tokyo','163-8001','JP',TRUE),
('ADDR010','CUST009','hq',       '1 Liberty Plaza',NULL,                'New York','NY','10006','US',TRUE),
('ADDR011','CUST010','hq',       '8 Marina Blvd','#05-02',              'Singapore','Central','018981','SG',TRUE);

-- =====================================================================
-- 15. CAMPAIGNS
-- =====================================================================
INSERT INTO `acme_corp.campaigns`
(campaign_id, name, channel, start_date, end_date, budget_usd, spend_usd, owner_employee_id) VALUES
('CAMP001','Q1 2025 GraphRAG Webinar Series','email',   DATE '2025-01-15',DATE '2025-03-31', 25000, 23400,'EMP009'),
('CAMP002','AWS re:Invent 2024 Booth','event',          DATE '2024-12-01',DATE '2024-12-08',320000,318700,'EMP006'),
('CAMP003','Paid Search - Graph Database','paid_search',DATE '2025-01-01',DATE '2025-12-31',480000,112000,'EMP009'),
('CAMP004','SEO Content Hub 2025','content',            DATE '2025-02-01',DATE '2025-12-31', 90000, 34500,'EMP010'),
('CAMP005','LinkedIn ABM - Enterprise','social',        DATE '2025-03-01',DATE '2025-09-30',180000, 98000,'EMP006'),
('CAMP006','Neo4j NODES 2024 Sponsorship','event',      DATE '2024-10-01',DATE '2024-11-30', 75000, 75000,'EMP009'),
('CAMP007','EMEA Field Marketing Roadshow','event',     DATE '2025-04-01',DATE '2025-06-30',140000,139500,'EMP008'),
('CAMP008','Developer Newsletter','email',              DATE '2024-01-01',DATE '2025-12-31', 40000, 28000,'EMP010'),
('CAMP009','Summer Pipeline Push','paid_search',        DATE '2025-06-01',DATE '2025-08-31',120000,120300,'EMP009'),
('CAMP010','APAC Launch','social',                      DATE '2025-02-14',DATE '2025-05-31', 85000, 81200,'EMP011');

-- =====================================================================
-- 16. LEADS
-- =====================================================================
INSERT INTO `acme_corp.leads`
(lead_id, first_name, last_name, email, company, title, source, campaign_id, status, score, assigned_to, created_at, converted_customer_id, converted_at) VALUES
('LEAD001','Mia','Wallace','mwallace@bigbank.example','Big Bank Corp','Data Architect','web','CAMP004','qualified',78,'EMP007', TIMESTAMP '2025-02-10 14:22:00 UTC',NULL,NULL),
('LEAD002','Vincent','Vega','vvega@retailco.example','RetailCo','Head of BI','event','CAMP002','converted',92,'EMP006', TIMESTAMP '2024-12-05 10:15:00 UTC','CUST010', TIMESTAMP '2024-08-05 09:00:00 UTC'),
('LEAD003','Jules','Winnfield','jwinnfield@fintechlabs.example','Fintech Labs','VP Engineering','web','CAMP001','qualified',84,'EMP007', TIMESTAMP '2025-03-01 09:30:00 UTC',NULL,NULL),
('LEAD004','Mr','Pink','pink@startup.example','Stealth Startup','Founder','referral',NULL,'contacted',45,'EMP008', TIMESTAMP '2025-04-12 11:00:00 UTC',NULL,NULL),
('LEAD005','Butch','Coolidge','butch@logisticsinc.example','Logistics Inc','CTO','outbound',NULL,'disqualified',28,'EMP007', TIMESTAMP '2025-05-05 16:45:00 UTC',NULL,NULL),
('LEAD006','Marsellus','Wallace','marsellus@enterprise-co.example','Enterprise Co','CIO','event','CAMP006','qualified',88,'EMP006', TIMESTAMP '2024-10-15 13:00:00 UTC',NULL,NULL),
('LEAD007','Fabienne','Plamondon','fabienne@globalmedia.example','Global Media','Director of Data','paid_search','CAMP003','new',55,'EMP008', TIMESTAMP '2025-07-02 08:20:00 UTC',NULL,NULL),
('LEAD008','Lance','Spencer','lance@healthtech.example','HealthTech','Principal Engineer','web','CAMP004','qualified',70,'EMP007', TIMESTAMP '2025-08-14 15:10:00 UTC',NULL,NULL),
('LEAD009','Honey','Bunny','hbunny@dinerco.example','DinerCo','Head of Engineering','ads','CAMP009','new',48,'EMP008', TIMESTAMP '2025-09-10 12:00:00 UTC',NULL,NULL),
('LEAD010','Ringo','Starr','ringo@apaccorp.example','APAC Corp','Data Platform Lead','social','CAMP010','qualified',81,'EMP011', TIMESTAMP '2025-04-22 09:00:00 UTC',NULL,NULL);

-- =====================================================================
-- 17. OPPORTUNITIES
-- =====================================================================
INSERT INTO `acme_corp.opportunities`
(opportunity_id, customer_id, name, stage, amount_usd, probability, close_date, owner_employee_id, source_lead_id, loss_reason, created_at, closed_at) VALUES
('OPP001','CUST001','Globex Platform Expansion 2025','closed_won', 850000, 1.00, DATE '2025-06-30','EMP006',NULL,NULL, TIMESTAMP '2025-03-15 09:00:00 UTC', TIMESTAMP '2025-06-29 17:00:00 UTC'),
('OPP002','CUST002','Initech Seat Upsell','closed_won', 120000, 1.00, DATE '2025-04-15','EMP007',NULL,NULL, TIMESTAMP '2025-02-01 09:00:00 UTC', TIMESTAMP '2025-04-14 17:00:00 UTC'),
('OPP003','CUST003','Soylent Renewal + Add-ons','negotiation', 480000, 0.75, DATE '2026-05-31','EMP008',NULL,NULL, TIMESTAMP '2026-01-10 09:00:00 UTC',NULL),
('OPP004','CUST004','Acme Widgets Pilot Expansion','proposal', 180000, 0.55, DATE '2026-06-30','EMP007',NULL,NULL, TIMESTAMP '2026-02-15 09:00:00 UTC',NULL),
('OPP005','CUST005','Stark Enterprise-wide Rollout','closed_won',1850000, 1.00, DATE '2025-09-30','EMP006',NULL,NULL, TIMESTAMP '2025-04-20 09:00:00 UTC', TIMESTAMP '2025-09-28 17:00:00 UTC'),
('OPP006','CUST006','Hooli Evaluation','discovery', 220000, 0.20, DATE '2026-09-30','EMP007',NULL,NULL, TIMESTAMP '2026-03-05 09:00:00 UTC',NULL),
('OPP007','CUST007','Umbrella Renewal','closed_lost',350000, 0.00, DATE '2025-05-31','EMP008',NULL,'competitor (chose in-house build)', TIMESTAMP '2025-01-12 09:00:00 UTC', TIMESTAMP '2025-05-30 17:00:00 UTC'),
('OPP008','CUST008','Tyrell APAC Expansion','proposal', 260000, 0.50, DATE '2026-07-31','EMP007',NULL,NULL, TIMESTAMP '2026-02-20 09:00:00 UTC',NULL),
('OPP009','CUST009','Massive Dynamic Multi-year','closed_won',2400000, 1.00, DATE '2025-12-20','EMP006',NULL,NULL, TIMESTAMP '2025-08-01 09:00:00 UTC', TIMESTAMP '2025-12-19 17:00:00 UTC'),
('OPP010','CUST010','Prometheus Pilot','discovery',  60000, 0.30, DATE '2026-08-31','EMP011','LEAD002',NULL, TIMESTAMP '2024-08-05 09:00:00 UTC',NULL);

-- =====================================================================
-- 18. SALES ACTIVITIES
-- =====================================================================
INSERT INTO `acme_corp.sales_activities`
(activity_id, opportunity_id, lead_id, contact_id, employee_id, activity_type, subject, notes, activity_at, duration_minutes) VALUES
('ACT001','OPP001',NULL,'CONTACT001','EMP006','meeting','Expansion scoping call','Identified 3 new use cases; graph analytics focus', TIMESTAMP '2025-04-02 15:00:00 UTC',60),
('ACT002','OPP001',NULL,'CONTACT002','EMP006','demo','Technical deep-dive','Demoed GDS algorithms; strong interest', TIMESTAMP '2025-04-18 14:00:00 UTC',75),
('ACT003','OPP002',NULL,'CONTACT003','EMP007','call','Renewal discussion','Agreed on 2x seat expansion', TIMESTAMP '2025-03-10 10:00:00 UTC',30),
('ACT004','OPP003',NULL,'CONTACT004','EMP008','meeting','Renewal negotiation','Pushing back on uplift; exec escalation needed', TIMESTAMP '2026-03-22 13:00:00 UTC',45),
('ACT005',NULL,'LEAD001',NULL,'EMP007','email','Discovery follow-up','Sent case studies and GraphRAG whitepaper', TIMESTAMP '2025-02-12 09:15:00 UTC',5),
('ACT006','OPP005',NULL,'CONTACT006','EMP006','meeting','QBR + expansion','Presented roadmap; got exec sponsor buy-in', TIMESTAMP '2025-07-10 14:00:00 UTC',90),
('ACT007','OPP007',NULL,'CONTACT008','EMP008','call','Save attempt','Lost to in-house build; postmortem scheduled', TIMESTAMP '2025-05-20 16:00:00 UTC',45),
('ACT008','OPP009',NULL,'CONTACT010','EMP006','meeting','Multi-year contract review','Legal reviewed; pending final signature', TIMESTAMP '2025-11-15 11:00:00 UTC',60),
('ACT009','OPP010',NULL,'CONTACT011','EMP011','demo','Pilot kickoff','Walked through Neocarta use case', TIMESTAMP '2024-09-10 09:00:00 UTC',50),
('ACT010','OPP006',NULL,'CONTACT007','EMP007','email','Re-engagement','Reply after 3 weeks of silence; scheduling next call', TIMESTAMP '2026-03-25 08:30:00 UTC',5);

-- =====================================================================
-- 19. QUOTES
-- =====================================================================
INSERT INTO `acme_corp.quotes`
(quote_id, opportunity_id, version, total_amount_usd, discount_pct, valid_until, status, sent_at, created_by) VALUES
('Q001','OPP001',1, 900000,  5.0, DATE '2025-05-31','accepted', TIMESTAMP '2025-04-20 12:00:00 UTC','EMP006'),
('Q002','OPP001',2, 850000, 10.0, DATE '2025-06-15','accepted', TIMESTAMP '2025-05-10 12:00:00 UTC','EMP006'),
('Q003','OPP002',1, 120000,  0.0, DATE '2025-04-30','accepted', TIMESTAMP '2025-03-15 12:00:00 UTC','EMP007'),
('Q004','OPP003',1, 520000,  0.0, DATE '2026-03-31','sent',     TIMESTAMP '2026-02-10 12:00:00 UTC','EMP008'),
('Q005','OPP003',2, 480000,  8.0, DATE '2026-05-15','sent',     TIMESTAMP '2026-03-18 12:00:00 UTC','EMP008'),
('Q006','OPP004',1, 195000,  7.5, DATE '2026-06-30','sent',     TIMESTAMP '2026-03-01 12:00:00 UTC','EMP007'),
('Q007','OPP005',1,2000000, 10.0, DATE '2025-08-31','accepted', TIMESTAMP '2025-06-15 12:00:00 UTC','EMP006'),
('Q008','OPP005',2,1850000, 17.0, DATE '2025-10-15','accepted', TIMESTAMP '2025-08-20 12:00:00 UTC','EMP006'),
('Q009','OPP008',1, 280000,  7.1, DATE '2026-06-30','sent',     TIMESTAMP '2026-03-05 12:00:00 UTC','EMP007'),
('Q010','OPP009',1,2600000,  7.7, DATE '2025-12-31','accepted', TIMESTAMP '2025-10-01 12:00:00 UTC','EMP006');

-- =====================================================================
-- 20. PRODUCT CATEGORIES
-- =====================================================================
INSERT INTO `acme_corp.product_categories`
(category_id, name, parent_category_id, description) VALUES
('CAT001','Platform',                NULL, 'Core graph platform products'),
('CAT002','Graph Database',          'CAT001','Managed and self-hosted graph DB editions'),
('CAT003','Graph Analytics',         'CAT001','GDS and analytics add-ons'),
('CAT004','GenAI Add-ons',           'CAT001','GraphRAG and LLM-related tools'),
('CAT005','Tools',                   NULL, 'Developer and ops tools'),
('CAT006','Developer Tools',         'CAT005','IDE, CLI, MCP servers'),
('CAT007','Data Integration',        'CAT005','Connectors and ETL'),
('CAT008','Services',                NULL,'Professional services offerings'),
('CAT009','Training',                'CAT008','Courses and certifications'),
('CAT010','Consulting',              'CAT008','Implementation and advisory');

-- =====================================================================
-- 21. PRODUCTS
-- =====================================================================
INSERT INTO `acme_corp.products`
(product_id, sku, name, category_id, description, list_price_usd, cost_usd, is_active, tags, launched_at) VALUES
('PROD001','ACME-DB-STD',  'Acme Graph DB Standard','CAT002','Self-hosted graph DB, up to 100GB',    36000,  7200,TRUE,['on_prem','standard'],       DATE '2015-06-01'),
('PROD002','ACME-DB-ENT',  'Acme Graph DB Enterprise','CAT002','HA clustering, unlimited scale',   180000, 22000,TRUE,['on_prem','enterprise','ha'],DATE '2016-02-15'),
('PROD003','ACME-CLOUD',   'Acme Cloud',             'CAT002','Managed graph DB on AWS/GCP/Azure',   60000,  9500,TRUE,['saas','managed'],           DATE '2019-09-10'),
('PROD004','ACME-GDS',     'Acme Graph Data Science','CAT003','Graph algorithms and embeddings',     48000,  6100,TRUE,['analytics','ml'],           DATE '2020-04-22'),
('PROD005','ACME-RAG',     'Acme GraphRAG',          'CAT004','Retrieval augmented generation over graphs',72000, 9400,TRUE,['genai','rag','llm'],  DATE '2024-03-05'),
('PROD006','ACME-BLOOM',   'Acme Bloom',             'CAT006','Visual graph exploration UI',         12000,  2400,TRUE,['visualization'],            DATE '2018-11-01'),
('PROD007','ACME-MCP',     'Acme MCP Server',        'CAT006','Model Context Protocol server for LLM agents',18000,3200,TRUE,['mcp','agent','llm'],DATE '2025-01-20'),
('PROD008','ACME-CDC',     'Acme Change Data Capture','CAT007','Kafka/Pulsar CDC connector',         24000,  3800,TRUE,['cdc','streaming'],          DATE '2021-07-14'),
('PROD009','ACME-CERT',    'Acme Certification',     'CAT009','Certified Graph Engineer exam',        600,   120,TRUE,['training','cert'],          DATE '2017-05-10'),
('PROD010','ACME-PS-IMPL', 'Implementation Services','CAT010','Packaged implementation (10 wk)',    250000, 95000,TRUE,['services','implementation'],DATE '2016-01-01');

-- =====================================================================
-- 22. SUBSCRIPTIONS
-- =====================================================================
INSERT INTO `acme_corp.subscriptions`
(subscription_id, customer_id, product_id, plan_name, seats, mrr_usd, arr_usd, billing_cycle, start_date, renewal_date, cancelled_date, status, owner_employee_id) VALUES
('SUB001','CUST001','PROD002','Enterprise Tier 3', 150, 70833,  850000,'annual',DATE '2024-07-01',DATE '2026-07-01',NULL,                 'active',   'EMP006'),
('SUB002','CUST001','PROD004','GDS Enterprise',     50,  8333,  100000,'annual',DATE '2025-01-01',DATE '2026-01-01',NULL,                 'active',   'EMP006'),
('SUB003','CUST002','PROD003','Cloud Growth',       80, 10000,  120000,'annual',DATE '2024-05-01',DATE '2026-05-01',NULL,                 'active',   'EMP007'),
('SUB004','CUST003','PROD002','Enterprise Tier 2', 100, 40000,  480000,'annual',DATE '2023-06-01',DATE '2026-06-01',NULL,                 'active',   'EMP008'),
('SUB005','CUST004','PROD003','Cloud Pro',          40,  5000,   60000,'annual',DATE '2023-01-01',DATE '2026-01-01',NULL,                 'active',   'EMP007'),
('SUB006','CUST005','PROD002','Enterprise Tier 4', 300,154167, 1850000,'annual',DATE '2025-10-01',DATE '2028-10-01',NULL,                 'active',   'EMP006'),
('SUB007','CUST005','PROD005','GraphRAG Enterprise',50, 20000,  240000,'annual',DATE '2025-10-01',DATE '2026-10-01',NULL,                 'active',   'EMP006'),
('SUB008','CUST006','PROD003','Cloud Pro',          60,  6667,   80000,'annual',DATE '2024-03-01',DATE '2026-03-01',NULL,                 'active',   'EMP007'),
('SUB009','CUST007','PROD002','Enterprise Tier 1',  50, 15000,  180000,'annual',DATE '2022-06-01',DATE '2025-05-31',DATE '2025-05-31',    'cancelled','EMP008'),
('SUB010','CUST008','PROD003','Cloud Growth',       35,  4500,   54000,'annual',DATE '2024-01-01',DATE '2026-01-01',NULL,                 'active',   'EMP007'),
('SUB011','CUST010','PROD005','GraphRAG Trial',      5,  2000,   24000,'monthly',DATE '2024-09-01',DATE '2026-08-31',NULL,                'trialing', 'EMP011');

-- =====================================================================
-- 23. ORDERS
-- =====================================================================
INSERT INTO `acme_corp.orders`
(order_id, customer_id, order_date, status, currency, subtotal_usd, tax_usd, shipping_usd, total_usd, placed_by_contact_id, sales_rep_id) VALUES
('ORD001','CUST001',DATE '2025-06-30','delivered','USD', 850000,   0,0, 850000,'CONTACT001','EMP006'),
('ORD002','CUST001',DATE '2025-01-15','delivered','USD', 100000,   0,0, 100000,'CONTACT001','EMP006'),
('ORD003','CUST002',DATE '2025-04-15','delivered','USD', 120000,   0,0, 120000,'CONTACT003','EMP007'),
('ORD004','CUST003',DATE '2024-06-01','delivered','USD', 480000,   0,0, 480000,'CONTACT004','EMP008'),
('ORD005','CUST005',DATE '2025-09-30','delivered','USD',1850000,   0,0,1850000,'CONTACT006','EMP006'),
('ORD006','CUST005',DATE '2025-10-05','delivered','USD', 240000,   0,0, 240000,'CONTACT006','EMP006'),
('ORD007','CUST006',DATE '2024-03-01','delivered','USD',  80000,   0,0,  80000,'CONTACT007','EMP007'),
('ORD008','CUST008',DATE '2024-01-10','delivered','USD',  54000,   0,0,  54000,'CONTACT009','EMP007'),
('ORD009','CUST009',DATE '2025-12-20','delivered','USD',2400000,   0,0,2400000,'CONTACT010','EMP006'),
('ORD010','CUST004',DATE '2023-01-01','delivered','USD',  60000,   0,0,  60000,'CONTACT005','EMP007');

-- =====================================================================
-- 24. ORDER ITEMS
-- =====================================================================
INSERT INTO `acme_corp.order_items`
(order_item_id, order_id, product_id, quantity, unit_price_usd, discount_pct, line_total_usd) VALUES
('OI001','ORD001','PROD002',1,  944444, 10.00, 850000),
('OI002','ORD002','PROD004',1,  100000,  0.00, 100000),
('OI003','ORD003','PROD003',1,  120000,  0.00, 120000),
('OI004','ORD004','PROD002',1,  480000,  0.00, 480000),
('OI005','ORD005','PROD002',1, 2228916, 17.00,1850000),
('OI006','ORD006','PROD005',1,  240000,  0.00, 240000),
('OI007','ORD007','PROD003',1,   80000,  0.00,  80000),
('OI008','ORD008','PROD003',1,   54000,  0.00,  54000),
('OI009','ORD009','PROD002',1, 2600000,  7.69,2400000),
('OI010','ORD009','PROD010',1,  250000,  0.00, 250000),
('OI011','ORD010','PROD003',1,   60000,  0.00,  60000),
('OI012','ORD001','PROD009',5,     600,  0.00,   3000);

-- =====================================================================
-- 25. INVOICES
-- =====================================================================
INSERT INTO `acme_corp.invoices`
(invoice_id, customer_id, subscription_id, order_id, invoice_number, issue_date, due_date, amount_usd, tax_usd, total_usd, status, paid_at) VALUES
('INV001','CUST001','SUB001','ORD001','INV-2025-00001',DATE '2025-07-01',DATE '2025-07-31', 850000, 0, 850000,'paid',     TIMESTAMP '2025-07-20 10:00:00 UTC'),
('INV002','CUST001','SUB002','ORD002','INV-2025-00002',DATE '2025-01-16',DATE '2025-02-15', 100000, 0, 100000,'paid',     TIMESTAMP '2025-02-10 10:00:00 UTC'),
('INV003','CUST002','SUB003','ORD003','INV-2025-00003',DATE '2025-04-16',DATE '2025-05-16', 120000, 0, 120000,'paid',     TIMESTAMP '2025-05-05 10:00:00 UTC'),
('INV004','CUST003','SUB004','ORD004','INV-2024-00055',DATE '2024-06-02',DATE '2024-07-02', 480000, 0, 480000,'paid',     TIMESTAMP '2024-06-25 10:00:00 UTC'),
('INV005','CUST005','SUB006','ORD005','INV-2025-00078',DATE '2025-10-01',DATE '2025-10-31',1850000, 0,1850000,'paid',     TIMESTAMP '2025-10-20 10:00:00 UTC'),
('INV006','CUST005','SUB007','ORD006','INV-2025-00079',DATE '2025-10-06',DATE '2025-11-05', 240000, 0, 240000,'paid',     TIMESTAMP '2025-11-02 10:00:00 UTC'),
('INV007','CUST006','SUB008','ORD007','INV-2024-00022',DATE '2024-03-02',DATE '2024-04-01',  80000, 0,  80000,'paid',     TIMESTAMP '2024-03-28 10:00:00 UTC'),
('INV008','CUST008','SUB010','ORD008','INV-2024-00003',DATE '2024-01-11',DATE '2024-02-10',  54000, 0,  54000,'paid',     TIMESTAMP '2024-02-05 10:00:00 UTC'),
('INV009','CUST009',NULL,    'ORD009','INV-2025-00110',DATE '2025-12-21',DATE '2026-01-20',2400000, 0,2400000,'sent',     NULL),
('INV010','CUST004','SUB005','ORD010','INV-2023-00004',DATE '2023-01-02',DATE '2023-02-01',  60000, 0,  60000,'paid',     TIMESTAMP '2023-01-25 10:00:00 UTC');

-- =====================================================================
-- 26. PAYMENTS
-- =====================================================================
INSERT INTO `acme_corp.payments`
(payment_id, invoice_id, customer_id, payment_method, amount_usd, currency, processor, processor_transaction_id, status, paid_at) VALUES
('PAY001','INV001','CUST001','wire',  850000,'USD','bank',  'BNK-20250720-9911','succeeded', TIMESTAMP '2025-07-20 10:15:00 UTC'),
('PAY002','INV002','CUST001','wire',  100000,'USD','bank',  'BNK-20250210-3412','succeeded', TIMESTAMP '2025-02-10 10:05:00 UTC'),
('PAY003','INV003','CUST002','ach',   120000,'USD','stripe','ch_3NxyzInitech88','succeeded', TIMESTAMP '2025-05-05 10:02:00 UTC'),
('PAY004','INV004','CUST003','wire',  480000,'USD','bank',  'BNK-20240625-5501','succeeded', TIMESTAMP '2024-06-25 10:10:00 UTC'),
('PAY005','INV005','CUST005','wire', 1850000,'USD','bank',  'BNK-20251020-7788','succeeded', TIMESTAMP '2025-10-20 10:30:00 UTC'),
('PAY006','INV006','CUST005','wire',  240000,'USD','bank',  'BNK-20251102-7812','succeeded', TIMESTAMP '2025-11-02 10:10:00 UTC'),
('PAY007','INV007','CUST006','ach',    80000,'USD','stripe','ch_3LhooliA22xz',  'succeeded', TIMESTAMP '2024-03-28 10:00:00 UTC'),
('PAY008','INV008','CUST008','wire',   54000,'USD','bank',  'BNK-20240205-0001','succeeded', TIMESTAMP '2024-02-05 10:00:00 UTC'),
('PAY009','INV003','CUST002','ach',   120000,'USD','stripe','ch_3NxyzInitech89','refunded',  TIMESTAMP '2025-05-06 11:00:00 UTC'),
('PAY010','INV010','CUST004','card',   60000,'USD','stripe','ch_3Ka3AcmeWdgts', 'succeeded', TIMESTAMP '2023-01-25 10:00:00 UTC');

-- =====================================================================
-- 27. SUPPORT TICKETS
-- =====================================================================
INSERT INTO `acme_corp.support_tickets`
(ticket_id, customer_id, contact_id, subject, description, priority, category, status, assigned_to, created_at, first_response_at, resolved_at, csat_score) VALUES
('TICK001','CUST001','CONTACT002','Cluster replication lag','Seeing 30s+ replication lag on prod cluster','high','technical','solved','EMP004',        TIMESTAMP '2025-08-12 09:15:00 UTC', TIMESTAMP '2025-08-12 09:42:00 UTC', TIMESTAMP '2025-08-12 16:40:00 UTC',5),
('TICK002','CUST002','CONTACT003','Billing question on seat expansion','Need clarification on proration','normal','billing','solved','EMP011',       TIMESTAMP '2025-04-16 13:00:00 UTC', TIMESTAMP '2025-04-16 13:30:00 UTC', TIMESTAMP '2025-04-17 10:00:00 UTC',4),
('TICK003','CUST003','CONTACT004','GDS algorithm OOM','Louvain OOM on 2B edge graph','high','technical','solved','EMP003',                            TIMESTAMP '2025-10-02 11:00:00 UTC', TIMESTAMP '2025-10-02 11:15:00 UTC', TIMESTAMP '2025-10-03 18:00:00 UTC',5),
('TICK004','CUST004','CONTACT005','SSO integration help','Trying to configure Azure AD SSO','normal','technical','solved','EMP004',                    TIMESTAMP '2026-01-20 08:45:00 UTC', TIMESTAMP '2026-01-20 09:10:00 UTC', TIMESTAMP '2026-01-21 12:00:00 UTC',5),
('TICK005','CUST005','CONTACT006','Upgrade planning','Planning upgrade to v6.x','normal','technical','pending','EMP003',                              TIMESTAMP '2026-03-15 10:00:00 UTC', TIMESTAMP '2026-03-15 10:45:00 UTC', NULL,NULL),
('TICK006','CUST006','CONTACT007','Feature request: Vector index','Want pgvector-like HNSW','low','feature_request','open','EMP009',                   TIMESTAMP '2026-02-10 14:00:00 UTC', TIMESTAMP '2026-02-11 09:00:00 UTC', NULL,NULL),
('TICK007','CUST007','CONTACT008','Bug: import_text_to_kg duplicates','Same entity name duplicates across imports','urgent','bug','solved','EMP004', TIMESTAMP '2025-03-22 16:00:00 UTC', TIMESTAMP '2025-03-22 16:10:00 UTC', TIMESTAMP '2025-03-24 17:00:00 UTC',3),
('TICK008','CUST008','CONTACT009','Cloud region availability','Need Tokyo region','normal','technical','solved','EMP011',                             TIMESTAMP '2025-11-20 02:00:00 UTC', TIMESTAMP '2025-11-20 08:00:00 UTC', TIMESTAMP '2025-11-22 06:00:00 UTC',4),
('TICK009','CUST009','CONTACT010','Prod outage - connection refused','All app nodes cannot connect','urgent','technical','solved','EMP002',          TIMESTAMP '2025-12-28 03:10:00 UTC', TIMESTAMP '2025-12-28 03:14:00 UTC', TIMESTAMP '2025-12-28 05:30:00 UTC',5),
('TICK010','CUST010','CONTACT011','Trial extension request','Need 2 more weeks for POC','low','billing','new','EMP011',                                TIMESTAMP '2026-04-15 10:00:00 UTC', NULL, NULL, NULL);

-- =====================================================================
-- 28. TICKET COMMENTS
-- =====================================================================
INSERT INTO `acme_corp.ticket_comments`
(comment_id, ticket_id, author_type, author_id, body, is_internal, created_at) VALUES
('TCOM001','TICK001','customer','CONTACT002','Lag started around 08:50 UTC after deploy',FALSE, TIMESTAMP '2025-08-12 09:15:00 UTC'),
('TCOM002','TICK001','agent','EMP004','Checking replication logs, likely write-heavy txns',FALSE, TIMESTAMP '2025-08-12 09:42:00 UTC'),
('TCOM003','TICK001','agent','EMP004','Found runaway APOC job; tuned batch size',         FALSE, TIMESTAMP '2025-08-12 15:00:00 UTC'),
('TCOM004','TICK001','agent','EMP004','Escalating to eng mgmt for postmortem',            TRUE,  TIMESTAMP '2025-08-12 15:10:00 UTC'),
('TCOM005','TICK003','customer','CONTACT004','Graph has 2.1B relationships',              FALSE, TIMESTAMP '2025-10-02 11:05:00 UTC'),
('TCOM006','TICK003','agent','EMP003','Recommend projecting subgraph and tuning heap',    FALSE, TIMESTAMP '2025-10-02 11:15:00 UTC'),
('TCOM007','TICK007','customer','CONTACT008','This is blocking our pilot',                FALSE, TIMESTAMP '2025-03-22 16:05:00 UTC'),
('TCOM008','TICK007','agent','EMP004','Reproduced; entity resolution weak for drifted names. Workaround: pass allowed_relationships', FALSE, TIMESTAMP '2025-03-23 09:00:00 UTC'),
('TCOM009','TICK007','agent','EMP004','Filed internal bug BUG-4421',                      TRUE,  TIMESTAMP '2025-03-23 09:15:00 UTC'),
('TCOM010','TICK009','customer','CONTACT010','P1 - production down',                      FALSE, TIMESTAMP '2025-12-28 03:10:00 UTC'),
('TCOM011','TICK009','agent','EMP002','Paging on-call, investigating DNS',                FALSE, TIMESTAMP '2025-12-28 03:14:00 UTC'),
('TCOM012','TICK009','agent','EMP002','Root cause: expired TLS cert on LB. Rotated.',     FALSE, TIMESTAMP '2025-12-28 05:30:00 UTC');

-- =====================================================================
-- 29. PROJECTS
-- =====================================================================
INSERT INTO `acme_corp.projects`
(project_id, name, description, department_id, project_lead_id, status, start_date, target_end_date, actual_end_date, budget_usd, spend_usd) VALUES
('PROJ001','Neocarta Metadata Catalog','Internal catalog for BQ + Neo4j metadata','DEPT001','EMP004','active',    DATE '2025-01-15',DATE '2026-06-30',NULL,          450000,210000),
('PROJ002','GraphRAG Chapter / Book','Technical book on GraphRAG for O\'Reilly','DEPT001','EMP004','active',      DATE '2024-09-01',DATE '2026-09-30',NULL,           80000, 38000),
('PROJ003','v6 Platform Upgrade','Major platform version upgrade','DEPT001','EMP002','active',                    DATE '2025-06-01',DATE '2026-09-30',NULL,         2400000,980000),
('PROJ004','EMEA Sales Ramp','Hire and onboard 8 AEs in EMEA','DEPT003','EMP006','completed',                     DATE '2024-09-01',DATE '2025-03-31',DATE '2025-03-28', 600000,584000),
('PROJ005','Support Tooling Refresh','Zendesk -> new stack migration','DEPT006',NULL,'planned',                    DATE '2026-07-01',DATE '2027-03-31',NULL,          320000,     0),
('PROJ006','Q2 Marketing Site Redesign','New site with personalization','DEPT004','EMP010','completed',           DATE '2025-02-01',DATE '2025-05-31',DATE '2025-06-10',180000,195000),
('PROJ007','SOC2 Type II Readiness','Audit prep and controls','DEPT010',NULL,'active',                             DATE '2025-10-01',DATE '2026-06-30',NULL,          260000, 92000),
('PROJ008','APAC GTM Launch','Go-to-market plan for APAC','DEPT003','EMP011','active',                            DATE '2024-07-01',DATE '2026-06-30',NULL,          750000,380000),
('PROJ009','Pricing Model Overhaul','Move to usage-based component','DEPT007',NULL,'on_hold',                      DATE '2025-04-01',DATE '2025-12-31',NULL,          120000, 45000),
('PROJ010','Leaver Offboarding Automation','HRIS -> IT automation','DEPT008',NULL,'planned',                       DATE '2026-05-01',DATE '2026-09-30',NULL,           70000,     0);

-- =====================================================================
-- 30. PROJECT ASSIGNMENTS
-- =====================================================================
INSERT INTO `acme_corp.project_assignments`
(assignment_id, project_id, employee_id, role, allocation_pct, start_date, end_date) VALUES
('PA001','PROJ001','EMP004','Tech Lead',         70, DATE '2025-01-15',NULL),
('PA002','PROJ001','EMP003','Architect',         30, DATE '2025-01-15',NULL),
('PA003','PROJ002','EMP004','Author',            20, DATE '2024-09-01',NULL),
('PA004','PROJ003','EMP002','Program Lead',      50, DATE '2025-06-01',NULL),
('PA005','PROJ003','EMP003','Senior Engineer',   60, DATE '2025-06-01',NULL),
('PA006','PROJ003','EMP005','Engineer',          40, DATE '2025-06-01',NULL),
('PA007','PROJ006','EMP010','Lead Designer',     80, DATE '2025-02-01',DATE '2025-06-10'),
('PA008','PROJ008','EMP011','APAC Lead',        100, DATE '2024-07-01',NULL),
('PA009','PROJ004','EMP006','Exec Sponsor',      20, DATE '2024-09-01',DATE '2025-03-28'),
('PA010','PROJ007','EMP004','Security Reviewer', 10, DATE '2025-10-01',NULL);

-- =====================================================================
-- 31. VENDORS
-- =====================================================================
INSERT INTO `acme_corp.vendors`
(vendor_id, name, category, contact_email, contact_phone, country, onboarded_date, status, risk_rating) VALUES
('VEN001','AWS',            'saas',       'enterprise@amazon.com','+1-888-555-2001','US', DATE '2015-04-01','active',  'low'),
('VEN002','Snowflake',      'saas',       'ae-acme@snowflake.example','+1-844-555-2002','US', DATE '2019-10-10','active','low'),
('VEN003','Datadog',        'saas',       'support@datadog.example','+1-866-555-2003','US', DATE '2018-05-20','active', 'low'),
('VEN004','Zendesk',        'saas',       'billing@zendesk.example','+1-415-555-2004','US', DATE '2017-02-15','active', 'low'),
('VEN005','WeWork',         'facilities', 'sf@wework.example','+1-415-555-2005','US',       DATE '2016-06-01','inactive','medium'),
('VEN006','Deloitte',       'consulting', 'acme-team@deloitte.example','+1-212-555-2006','US',DATE '2020-01-15','active','medium'),
('VEN007','Dell',           'hardware',   'acme@dell.example','+1-800-555-2007','US',       DATE '2016-03-10','active', 'low'),
('VEN008','Contentful',     'saas',       'success@contentful.example','+49-30-555-2008','DE',DATE '2022-04-05','active','low'),
('VEN009','HashiCorp',      'saas',       'sales@hashicorp.example','+1-415-555-2009','US', DATE '2020-08-22','active', 'low'),
('VEN010','Stealth Pen Test','consulting','contact@stealthpt.example','+44-20-5555-2010','GB',DATE '2025-09-01','pending_review','high');

-- =====================================================================
-- 32. VENDOR CONTRACTS
-- =====================================================================
INSERT INTO `acme_corp.vendor_contracts`
(contract_id, vendor_id, owner_employee_id, start_date, end_date, annual_spend_usd, currency, auto_renew, status, signed_at) VALUES
('VC001','VEN001','EMP002', DATE '2024-01-01',DATE '2026-12-31', 3200000,'USD',TRUE, 'active',    TIMESTAMP '2023-12-15 10:00:00 UTC'),
('VC002','VEN002','EMP001', DATE '2024-06-01',DATE '2026-05-31',  480000,'USD',TRUE, 'active',    TIMESTAMP '2024-05-20 10:00:00 UTC'),
('VC003','VEN003','EMP002', DATE '2025-01-01',DATE '2025-12-31',  260000,'USD',TRUE, 'active',    TIMESTAMP '2024-12-10 10:00:00 UTC'),
('VC004','VEN004','EMP011', DATE '2024-03-01',DATE '2026-02-28',  120000,'USD',FALSE,'active',    TIMESTAMP '2024-02-20 10:00:00 UTC'),
('VC005','VEN005','EMP001', DATE '2023-07-01',DATE '2024-12-31',  540000,'USD',FALSE,'expired',   TIMESTAMP '2023-06-15 10:00:00 UTC'),
('VC006','VEN006','EMP001', DATE '2025-02-01',DATE '2025-10-31',  420000,'USD',FALSE,'active',    TIMESTAMP '2025-01-20 10:00:00 UTC'),
('VC007','VEN007','EMP002', DATE '2024-09-01',DATE '2026-08-31',  180000,'USD',TRUE, 'active',    TIMESTAMP '2024-08-25 10:00:00 UTC'),
('VC008','VEN008','EMP010', DATE '2024-05-01',DATE '2026-04-30',   60000,'USD',TRUE, 'active',    TIMESTAMP '2024-04-10 10:00:00 UTC'),
('VC009','VEN009','EMP002', DATE '2024-10-01',DATE '2026-09-30',  220000,'USD',TRUE, 'active',    TIMESTAMP '2024-09-12 10:00:00 UTC'),
('VC010','VEN010','EMP001', DATE '2025-10-01',DATE '2026-03-31',   90000,'USD',FALSE,'active',    TIMESTAMP '2025-09-20 10:00:00 UTC');

-- =====================================================================
-- 33. WEB EVENTS
-- =====================================================================
INSERT INTO `acme_corp.web_events`
(event_id, session_id, visitor_id, customer_id, event_type, page_url, referrer, utm_source, utm_medium, utm_campaign, device_type, country, event_at) VALUES
('EV001','SESS-1001','VIS-A001',NULL,        'page_view',  'https://acme.example/','https://google.com/','google','organic',NULL,               'desktop','US', TIMESTAMP '2025-09-01 14:22:11 UTC'),
('EV002','SESS-1001','VIS-A001',NULL,        'page_view',  'https://acme.example/products/graph-rag',  'https://acme.example/','google','organic',NULL,'desktop','US', TIMESTAMP '2025-09-01 14:24:03 UTC'),
('EV003','SESS-1001','VIS-A001',NULL,        'click',      'https://acme.example/products/graph-rag',  NULL,'google','organic',NULL,               'desktop','US', TIMESTAMP '2025-09-01 14:26:30 UTC'),
('EV004','SESS-1001','VIS-A001',NULL,        'form_submit','https://acme.example/demo-request',        NULL,'google','organic',NULL,               'desktop','US', TIMESTAMP '2025-09-01 14:28:40 UTC'),
('EV005','SESS-1002','VIS-A002','CUST002',   'page_view',  'https://acme.example/docs/cypher',          'https://twitter.com/','twitter','social','CAMP008','mobile','US', TIMESTAMP '2025-09-02 09:05:00 UTC'),
('EV006','SESS-1003','VIS-A003',NULL,        'page_view',  'https://acme.example/blog/graphrag-intro',  'https://news.ycombinator.com/','hn','referral',NULL,'desktop','GB',TIMESTAMP '2025-09-03 18:00:00 UTC'),
('EV007','SESS-1004','VIS-A004',NULL,        'signup',     'https://acme.example/signup',               NULL,'linkedin','paid','CAMP005',           'desktop','DE', TIMESTAMP '2025-09-05 11:45:00 UTC'),
('EV008','SESS-1005','VIS-A005','CUST005',   'page_view',  'https://acme.example/pricing',              'https://acme.example/','direct','direct',NULL,'desktop','US', TIMESTAMP '2025-09-10 10:10:00 UTC'),
('EV009','SESS-1006','VIS-A006',NULL,        'page_view',  'https://acme.example/events/nodes-2024',    'https://neo4j.com/','referral','referral','CAMP006','desktop','NL',TIMESTAMP '2024-10-15 14:00:00 UTC'),
('EV010','SESS-1007','VIS-A007',NULL,        'click',      'https://acme.example/products/mcp-server',  NULL,'google','cpc','CAMP003',              'desktop','US', TIMESTAMP '2025-10-01 12:30:00 UTC'),
('EV011','SESS-1008','VIS-A008',NULL,        'page_view',  'https://acme.example/ja/',                  'https://google.co.jp/','google','organic',NULL,'mobile','JP', TIMESTAMP '2025-11-05 07:15:00 UTC'),
('EV012','SESS-1009','VIS-A009',NULL,        'form_submit','https://acme.example/contact-sales',        NULL,'linkedin','paid','CAMP005',           'desktop','SG', TIMESTAMP '2025-11-12 05:00:00 UTC'),
('EV013','SESS-1010','VIS-A010',NULL,        'page_view',  'https://acme.example/customers/massive-dynamic','https://acme.example/customers/','direct','direct',NULL,'tablet','CA',TIMESTAMP '2025-12-01 20:00:00 UTC'),
('EV014','SESS-1011','VIS-A011',NULL,        'signup',     'https://acme.example/signup',               NULL,'google','cpc','CAMP009',              'desktop','AU', TIMESTAMP '2026-01-15 22:30:00 UTC'),
('EV015','SESS-1012','VIS-A012','CUST010',   'page_view',  'https://acme.example/docs/mcp',             'https://acme.example/','direct','direct',NULL,'desktop','SG', TIMESTAMP '2026-02-20 03:00:00 UTC');