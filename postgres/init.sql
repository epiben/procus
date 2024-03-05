-- SCHEMA
CREATE TABLE public.recipients (
-- DDL

CREATE SCHEMA prod;
CREATE SCHEMA history;


---- Recipients
CREATE TABLE prod.recipients (
    recipient_id SERIAL PRIMARY KEY,
    phone_number text UNIQUE NOT NULL,
    full_name text NOT NULL,
    created_datetime timestamp with time zone DEFAULT now()
);
ALTER TABLE prod.recipients OWNER TO postgres;


---- Instruments
CREATE TABLE prod.instruments (
    instrument_id SERIAL PRIMARY KEY,
    instrument_name text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    updated_datetime timestamp with time zone DEFAULT now(),
    updated_by TEXT DEFAULT 'init'
);
ALTER TABLE prod.instruments OWNER TO postgres;

------ History table
CREATE TABLE history.instruments (
	LIKE prod.instruments INCLUDING ALL EXCLUDING INDEXES
);
ALTER TABLE history.instruments OWNER TO postgres;

CREATE OR REPLACE FUNCTION log_instrument_changes()
  RETURNS TRIGGER
  LANGUAGE PLPGSQL
  AS
$$
BEGIN
    INSERT INTO history.instruments(
        instrument_id
        , instrument_name
        , is_active
        , updated_datetime
        , updated_by
    )
    VALUES (
        OLD.instrument_id
        , OLD.instrument_name
        , OLD.is_active
        , now()
        , 'app'
    );

	RETURN NEW;
END;
$$;

CREATE TRIGGER instrument_changes
BEFORE UPDATE
ON prod.instruments
FOR EACH ROW
EXECUTE PROCEDURE log_instrument_changes();


---- Items
CREATE TABLE prod.items (
    item_id SERIAL PRIMARY KEY,
    instrument_id integer REFERENCES prod.instruments (instrument_id),
    item_text text NOT NULL,
    updated_datetime timestamp with time zone DEFAULT now(),
    updated_by TEXT DEFAULT 'init'
);
ALTER TABLE prod.items OWNER TO postgres;


---- Iterations
CREATE TABLE prod.iterations (
    iteration_id SERIAL PRIMARY KEY,
    instrument_id integer REFERENCES prod.instruments (instrument_id),
    phone_number text NOT NULL REFERENCES prod.recipients (phone_number),
    message_body text NOT NULL,
    is_open boolean DEFAULT false NOT NULL,
    opens_datetime timestamp with time zone NOT NULL,
    updated_datetime timestamp with time zone DEFAULT now() NOT NULL,
    updated_by TEXT DEFAULT 'init'
);
ALTER TABLE prod.iterations OWNER TO postgres;
CREATE INDEX idx__is_open ON prod.iterations (is_open) WHERE is_open is not true;
    -- partial index, faster than full index

------ History table
CREATE TABLE history.iterations (
    LIKE prod.iterations INCLUDING ALL EXCLUDING INDEXES
);
ALTER TABLE history.iterations OWNER TO postgres;

CREATE OR REPLACE FUNCTION log_iteration_changes()
  RETURNS TRIGGER
  LANGUAGE PLPGSQL
  AS
$$
BEGIN
    INSERT INTO history.iterations(
        iteration_id
        , instrument_id
        , phone_number
        , message_body
        , is_open
        , opens_datetime
        , updated_datetime
        , updated_by
    )
    VALUES (
        OLD.iteration_id
        , OLD.instrument_id
        , OLD.phone_number
        , OLD.message_body
        , OLD.is_open
        , OLD.opens_datetime
        , now()
        , 'app'
    );

	RETURN NEW;
END;
$$;

CREATE TRIGGER iteration_changes
BEFORE UPDATE
ON prod.iterations
FOR EACH ROW
EXECUTE PROCEDURE log_iteration_changes();


---- Responses
CREATE TABLE prod.responses (
    response_id SERIAL PRIMARY KEY,
    phone_number text REFERENCES prod.recipients (phone_number),
    item_id integer REFERENCES prod.items (item_id),
    item_text text,
    opens_datetime timestamp with time zone,
    response integer,
    status text DEFAULT 'open',
    status_datetime timestamp with time zone DEFAULT now(),
    updated_by text DEFAULT 'init'
);
ALTER TABLE prod.responses OWNER TO postgres;

------ History table
CREATE TABLE history.responses (
    LIKE prod.responses INCLUDING ALL EXCLUDING INDEXES
);
ALTER TABLE history.responses OWNER TO postgres;

CREATE OR REPLACE FUNCTION log_response_changes()
  RETURNS TRIGGER
  LANGUAGE PLPGSQL
  AS
$$
BEGIN
    INSERT INTO history.responses(
        response_id
        , phone_number
        , item_id
        , item_text
        , opens_datetime
        , response
        , status
        , status_datetime
        , updated_by
    )
    VALUES (
        OLD.response_id
        , OLD.phone_number
        , OLD.item_id
        , OLD.item_text
        , OLD.opens_datetime
        , OLD.response
        , OLD.status
        , now()
        , 'app'
    );

	RETURN NEW;
END;
$$;

CREATE TRIGGER response_changes
BEFORE UPDATE
ON prod.responses
FOR EACH ROW
EXECUTE PROCEDURE log_response_changes();


---- Log
CREATE TABLE prod.log (
    id SERIAL PRIMARY KEY,
    level character varying(10),
    message text,
    created_at timestamp without time zone DEFAULT now()
);
ALTER TABLE prod.log OWNER TO postgres;


---- Messages
CREATE TABLE prod.messages (
    sent_datetime timestamp with time zone DEFAULT now() NOT NULL,
    phone_number text REFERENCES prod.recipients (phone_number),
    message_body text,
    direction text CHECK (direction IN ('outbound', 'inbound'))
);
ALTER TABLE prod.messages OWNER TO postgres;

COMMENT ON TABLE prod.messages IS
'Holds all in- and outbound messages with timestamp, but without any tracking of which belong together. Table is meant for documentation and data scrutiny.';


-- DML

---- Instruments
INSERT INTO prod.instruments (instrument_name, is_active)
VALUES ('EQ-5D-5L', true);


---- Items
INSERT INTO prod.items (instrument_id, item_text)
VALUES
    (1, concat_ws(E'\n',
        'Hvor store problemer har du med at gå omkring?',
        '1: Ingen',
        '2: Lidt',
        '3: Moderate',
        '4: Store',
        '5: Jeg kan ikke gå omkring'
    )),
    (1, concat_ws(E'\n',
        'Hvor store problemer har du med at vaske eller klæde dig på?',
        '1: Ingen',
        '2: Lidt',
        '3: Moderate',
        '4: Store',
        '5: Jeg kan ikke vaske mig eller klæde mig på'
    )),
    (1, concat_ws(E'\n',
        'Hvor store problemer har du med at udføre sædvanlige aktiviteter?',
        '1: Ingen',
        '2: Lidt',
        '3: Moderate',
        '4: Store',
        '5: Jeg kan ikke udføre sædvanlige aktiviteter'
    )),
    (1, concat_ws(E'\n',
        'Hvor store smerter/meget ubehag har du?',
        '1: Ingen',
        '2: Lidt',
        '3: Moderate',
        '4: Store',
        '5: Ekstreme'
    )),
    (1, concat_ws(E'\n',
        'I hvor høj grad er du ængstelig eller deprimeret?',
        '1: Det er jeg ikke',
        '2: Lidt',
        '3: Moderate',
        '4: Store',
        '5: Ekstremt'
    ));


---- Dummy person, useful for cURL-based querying
INSERT INTO prod.recipients (phone_number, full_name)
VALUES ('4500000000', 'McUrl');

INSERT INTO prod.iterations (instrument_id, phone_number, message_body, is_open, opens_datetime)
SELECT
    1
    , phone_number
    , CONCAT('Dear ', full_name, '! Are you ready for another round? If so, reply with arbitrary messsage.')
    , true
    , now()
FROM prod.recipients;

INSERT INTO prod.responses (phone_number, item_text, item_id, opens_datetime, status)
SELECT
    '4500000000'
    , item_text
    , item_id
    , now()
    , 'open'
FROM prod.items;

INSERT INTO prod.responses (phone_number, item_text, item_id, opens_datetime, status)
VALUES ('4500000000', 'Thank you for your help! Reply with the word Restart to start over.', NULL, now(), 'open');
