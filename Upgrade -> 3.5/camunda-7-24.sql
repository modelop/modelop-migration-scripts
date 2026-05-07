insert into ACT_GE_SCHEMA_LOG values ('1100', CURRENT_TIMESTAMP, '7.22.0');

alter table ACT_RU_TASK add column TASK_STATE_ varchar(64);

alter table ACT_HI_TASKINST add column TASK_STATE_ varchar(64);

alter table ACT_RU_JOB add column BATCH_ID_ varchar(64);
alter table ACT_HI_JOB_LOG add column BATCH_ID_ varchar(64);

alter table ACT_HI_PROCINST add RESTARTED_PROC_INST_ID_ varchar(64);
create index ACT_IDX_HI_PRO_RST_PRO_INST_ID on ACT_HI_PROCINST(RESTARTED_PROC_INST_ID_);

insert into ACT_GE_SCHEMA_LOG
values ('1200', CURRENT_TIMESTAMP, '7.23.0');

alter table ACT_HI_COMMENT
    add column REV_ integer not null
        default 1;

alter table ACT_RU_EXECUTION add column PROC_DEF_KEY_ varchar(255);

insert into ACT_GE_SCHEMA_LOG
values ('1300', CURRENT_TIMESTAMP, '7.24.0');