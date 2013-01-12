create table if not exists patient
 (id integer primary key,
  name string,
  resparty integer references patient (id),
  birthday date,
  gender string,
  notes text);

create table if not exists journal
 (id integer primary key,
  patientid integer references patient (id),
  ts datetime,
  kind string,
  summary text,
  money currency);

create index if not exists journal_ts
 on journal(ts desc);

create table if not exists contact
 (journalid integer primary key,
  details text);

create table if not exists appointment
 (journalid integer primary key,
  duration integer,
  status string,
  kind string,
  notes text);

create table if not exists progress
 (journalid integer primary key,
  sub text,
  obj text,
  ass text,
  pln text);

create table if not exists rx
 (journalid integer primary key,
  disp string,
  sig string,
  refills string);

create table if not exists carrier
 (id integer primary key,
  name string,
  address text,
  phone string,
  web string,
  eclaim string);

create table if not exists plan
 (journalid integer primary key references journal(id),
  secondaryto integer references plan(id),
  carrierid integer references carrier(id),
  insuredid integer references patient(id),
  relationship string,
  student_status string,
  groupnum string,
  idnum string,
  employer string,
  deductible currency,
  maximum currency,
  prevent integer,
  basic integer,
  major integer,
  notes text);

create table if not exists claim
 (journalid integer primary key references journal (id),
  preauth bool,
  planid integer references plan (journalid),
  filed datetime,
  closed datetime,
  notes text);

create table if not exists claimform
 (claimid integer primary key references claim(journalid),
  -- from claimid -> preauth field
  type_of_transaction string,
  -- leave blank
  predetermination_number string,
  -- claimid -> planid -> carrierid -> name & address
  primary_payer_name_address text,
  -- if claimid -> planid -> secondary_to
  -- or if there is a plan with secondary_to == claimid -> planid
  -- set otherid to that plan ...
  -- whether we found other coverage
  other_coverage bool,
  -- otherid -> insuredid -> name
  other_subscriber_name string,
  -- otherid -> insuredid -> birthday
  other_subscriber_dob string,
  -- otherid -> insuredid -> gender
  other_subscriber_gender string,
  -- otherid -> idnum
  other_subscriber_id string,
  -- otherid -> groupnum
  other_subscriber_group string,
  -- otherid -> relationship
  relationship_to_other_subscriber string,
  -- otherid -> carrierid -> name & address
  other_carrier_name_address text,
  -- claimid -> planid -> insuredid -> name
  -- and lookup the most recent address in insuredid's journal
  primary_subscriber_name_address text,
  -- claimid -> planid -> insuredid -> birthday
  primary_subscriber_dob string,
  -- claimid -> planid -> insuredid -> gender
  primary_subscriber_gender string,
  -- claimid -> planid -> idnum
  primary_subscriber_id string,
  -- claimid -> planid -> groupnum
  primary_subscriber_group string,
  -- claimid -> planid -> employer
  primary_subscriber_employer string,
  -- claimid -> planid -> relationship
  relationship_to_primary_subscriber string,
  -- claimid -> planid -> student_status
  patient_student_status string,
  -- claimid -> journalid -> patientid -> name
  -- and lookup the most recent address in patientid's journal
  patient_name_address text,
  -- claimid -> journalid -> patientid -> birthday
  patient_dob string,
  -- claimid -> journalid -> patientid -> gender
  patient_gender string,
  -- claimid -> journalid -> patientid
  patient_id string,
  -- always zero
  other_fees currency default 0.00,
  -- sensible defaults, should be a way to modify
  missing_teeth string default '',
  remarks string default '',
  place_of_treatment string default 'office',
  number_of_enclosures string default NULL,
  orthodontic_treatment bool default false,
  orthodontic_start_date string default '',
  orthodontic_months_remaining string default '',
  prosthesis_replacement bool default NULL,
  prosthesis_original_date string default '',
  treatment_resulting_from string default '',
  date_of_accident string default '',
  state_of_accident string default '',
  -- office & provider information can be in config.py until further notice
  -- office information
  billing_name_address text,
  billing_npi string,
  billing_license string,
  billing_tin string,
  billing_phone string,
  billing_additional_id string,
  -- provider information
  treating_npi string,
  treating_license string,
  treating_address string,
  treating_specialty string,
  treating_phone string,
  treating_additional_id string);

create table if not exists cdt
 (id integer primary key,
  nomenclature string);

create table if not exists fees
 (id integer primary key,
  schedule string,
  code references cdt(id),
  fee currency);

create table if not exists tx
 (id integer primary key,
  journalid integer references journal (id),
  patientid integer references patient (id),
  appointmentid integer references appointment (id),
  claimid integer references claim (id),
  summary string,
  code integer,
  tooth string,
  surf string,
  fee currency,
  allowed currency,
  inspaid currency,
  ptpaid currency);
