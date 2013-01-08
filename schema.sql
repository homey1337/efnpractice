create table if not exists patient
 (id integer primary key,
  name string,
  resparty integer references patient (id),
  birthday date,
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
 (id integer primary key,
  journalid integer references journal(id),
  prim integer references plan(id),
  carrierid integer references carrier(id),
  insuredid integer references patient(id),
  groupnum string,
  idnum string,
  deductible currency,
  maximum currency,
  prevent integer,
  basic integer,
  major integer,
  notes text);

create table if not exists claim
 (id integer primary key,
  planid integer references plan (id),
  journalid integer references journal (id),
  filed datetime,
  closed datetime,
  notes text);

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
