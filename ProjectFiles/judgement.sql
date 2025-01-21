-- Create a warehouse
CREATE WAREHOUSE IF NOT EXISTS LEGAL_DATA_WAREHOUSE
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE;

-- Create a database
CREATE DATABASE IF NOT EXISTS LEGAL_DATA_DB;

-- Use the database
USE DATABASE LEGAL_DATA_DB;

-- Create a schema
CREATE SCHEMA IF NOT EXISTS LEGAL_DATA_SCHEMA;

-- Use the schema
USE SCHEMA LEGAL_DATA_SCHEMA;


CREATE TABLE IF NOT EXISTS judgements (
  "File Name" TEXT,
  "Extracted Text" TEXT
);



CREATE OR REPLACE STAGE LEGAL_DATA_STAGE
FILE_FORMAT = (TYPE = 'csv');

CREATE OR REPLACE FILE FORMAT judgements_format
  TYPE = 'CSV'
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  SKIP_HEADER = 1
  NULL_IF = ('');


COPY INTO LEGAL_DATA_SCHEMA.judgements ("File Name", "Extracted Text")
FROM @LEGAL_DATA_STAGE/cleaned_dataset_0.csv
FILE_FORMAT = judgements_format
ON_ERROR = 'CONTINUE';

COPY INTO LEGAL_DATA_SCHEMA.judgements ("File Name", "Extracted Text")
FROM @LEGAL_DATA_STAGE/cleaned_dataset_1.csv
FILE_FORMAT = judgements_format
ON_ERROR = 'CONTINUE';


COPY INTO LEGAL_DATA_SCHEMA.judgements ("File Name", "Extracted Text")
FROM @LEGAL_DATA_STAGE/cleaned_dataset_2.csv
FILE_FORMAT = judgements_format
ON_ERROR = 'CONTINUE';

COPY INTO LEGAL_DATA_SCHEMA.judgements ("File Name", "Extracted Text")
FROM @LEGAL_DATA_STAGE/cleaned_dataset_3.csv
FILE_FORMAT = judgements_format
ON_ERROR = 'CONTINUE';

COPY INTO LEGAL_DATA_SCHEMA.judgements ("File Name", "Extracted Text")
FROM @LEGAL_DATA_STAGE/cleaned_dataset_4.csv
FILE_FORMAT = judgements_format
ON_ERROR = 'CONTINUE';




select count(*) from judgements;
ALTER TABLE judgements RENAME COLUMN "Extracted Text" TO extracted_text;
ALTER TABLE judgements RENAME COLUMN "File Name" TO file_name;




CREATE OR REPLACE CORTEX SEARCH SERVICE LEGAL_JUDGEMENTS_CORTEX_SEARCH_SERVICE
  ON extracted_text
  WAREHOUSE = LEGAL_DATA
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
AS (
  SELECT extracted_text, file_name
  FROM LEGAL_DATA_SCHEMA.judgements
);

