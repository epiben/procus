-- Extensions
-- CREATE EXTENSION IF NOT EXISTS system_stats;

CREATE EXTENSION IF NOT EXISTS temporal_tables;
-- see https://clarkdave.net/2015/02/historical-records-with-postgresql-and-temporal-tables-and-sql-2011/

-- Schemas

CREATE SCHEMA prod;
CREATE SCHEMA history;


-- Recipients
CREATE TABLE prod.recipients (
    recipient_id SERIAL PRIMARY KEY,
    phone_number text UNIQUE NOT NULL,
    full_name text NOT NULL,
    created_datetime timestamp with time zone DEFAULT now()
);
ALTER TABLE prod.recipients OWNER TO postgres;


-- Instruments
CREATE TABLE prod.instruments (
    instrument_id SERIAL PRIMARY KEY,
    instrument_name text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_datetime timestamp with time zone NOT NULL DEFAULT now(),
    updated_by TEXT DEFAULT 'init',
    sys_period tstzrange NOT NULL DEFAULT tstzrange(current_timestamp, NULL)
);
ALTER TABLE prod.instruments OWNER TO postgres;

CREATE TABLE history.instruments (
	LIKE prod.instruments INCLUDING ALL EXCLUDING INDEXES
);
ALTER TABLE history.instruments OWNER TO postgres;

CREATE TRIGGER versioning_changes
BEFORE UPDATE OR DELETE ON prod.instruments
FOR EACH ROW EXECUTE PROCEDURE versioning(
    'sys_period', 'history.instruments', true
);


-- Items
CREATE TABLE prod.items (
    item_id SERIAL PRIMARY KEY,
    instrument_id integer REFERENCES prod.instruments (instrument_id),
    item_text text NOT NULL,
    created_datetime timestamp with time zone DEFAULT now(),
    updated_by TEXT DEFAULT 'init',
    sys_period tstzrange NOT NULL DEFAULT tstzrange(current_timestamp, NULL)
);
ALTER TABLE prod.items OWNER TO postgres;

CREATE TABLE history.items (
    LIKE prod.items INCLUDING ALL EXCLUDING INDEXES
);
ALTER TABLE history.items OWNER TO postgres;

CREATE TRIGGER versioning_changes
BEFORE UPDATE OR DELETE ON prod.items
FOR EACH ROW EXECUTE PROCEDURE versioning(
    'sys_period', 'history.items', true
);


-- Iterations
CREATE TABLE prod.iterations (
    iteration_id SERIAL PRIMARY KEY,
    instrument_id integer REFERENCES prod.instruments (instrument_id),
    phone_number text NOT NULL REFERENCES prod.recipients (phone_number),
    message_body text NOT NULL,
    is_open boolean DEFAULT false NOT NULL,
    opens_datetime timestamp with time zone NOT NULL,
    created_datetime timestamp with time zone DEFAULT now() NOT NULL,
    updated_by TEXT DEFAULT 'init',
    sys_period tstzrange NOT NULL DEFAULT tstzrange(current_timestamp, NULL)
);
ALTER TABLE prod.iterations OWNER TO postgres;
CREATE INDEX idx__is_open ON prod.iterations (is_open) WHERE is_open is not true;
    -- partial index, faster than full index

CREATE TABLE history.iterations (
    LIKE prod.iterations INCLUDING ALL EXCLUDING INDEXES
);
ALTER TABLE history.iterations OWNER TO postgres;

CREATE TRIGGER versioning_changes
BEFORE UPDATE OR DELETE ON prod.iterations
FOR EACH ROW EXECUTE PROCEDURE versioning(
    'sys_period', 'history.iterations', true
);


-- Responses
CREATE TABLE prod.responses (
    response_id SERIAL PRIMARY KEY,
    phone_number text REFERENCES prod.recipients (phone_number),
    item_id integer REFERENCES prod.items (item_id),
    item_text text,
    opens_datetime timestamp with time zone,
    response integer,
    status text DEFAULT 'open',
    created_datetime timestamp with time zone DEFAULT now(),
    updated_by text DEFAULT 'init',
    sys_period tstzrange NOT NULL DEFAULT tstzrange(current_timestamp, NULL)
);
ALTER TABLE prod.responses OWNER TO postgres;

CREATE TABLE history.responses (
    LIKE prod.responses INCLUDING ALL EXCLUDING INDEXES
);
ALTER TABLE history.responses OWNER TO postgres;

CREATE TRIGGER versioning_changes
BEFORE UPDATE OR DELETE ON prod.responses
FOR EACH ROW EXECUTE PROCEDURE versioning(
    'sys_period', 'history.responses', true
);


-- Log
CREATE TABLE prod.log (
    id SERIAL PRIMARY KEY,
    level character varying(10),
    message text,
    created_at timestamp without time zone DEFAULT now()
);
ALTER TABLE prod.log OWNER TO postgres;


-- Messages
CREATE TABLE prod.messages (
    message_id SERIAL PRIMARY KEY,
    sent_datetime timestamp with time zone DEFAULT now() NOT NULL,
    phone_number text REFERENCES prod.recipients (phone_number),
    message_body text,
    direction text CHECK (direction IN ('outbound', 'inbound'))
);
ALTER TABLE prod.messages OWNER TO postgres;

COMMENT ON TABLE prod.messages IS
'Holds all in- and outbound messages with timestamp, but without any tracking of which belong together. Table is meant for documentation and data scrutiny.';
