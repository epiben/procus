-- SCHEMA
CREATE TABLE public.recipients (
    recipient_id SERIAL PRIMARY KEY,
    phone_number text UNIQUE NOT NULL,
    full_name text NOT NULL,
    created_datetime timestamp with time zone DEFAULT now()
);
ALTER TABLE public.recipients OWNER TO postgres;


CREATE TABLE public.instruments (
    instrument_id SERIAL PRIMARY KEY,
    instrument_name text NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);
ALTER TABLE public.instruments OWNER TO postgres;


CREATE TABLE public.items (
    item_id SERIAL PRIMARY KEY,
    instrument_id integer REFERENCES public.instruments (instrument_id),
    item_text text NOT NULL
);
ALTER TABLE public.items OWNER TO postgres;


CREATE TABLE public.iterations (
    iteration_id SERIAL PRIMARY KEY,
    instrument_id integer REFERENCES public.instruments (instrument_id),
    phone_number text NOT NULL REFERENCES recipients (phone_number),
    message_body text NOT NULL,
    is_open boolean DEFAULT false NOT NULL,
    opens_datetime timestamp with time zone NOT NULL,
    created_datetime timestamp with time zone DEFAULT now() NOT NULL
);
ALTER TABLE public.iterations OWNER TO postgres;
CREATE INDEX idx__is_open ON public.iterations (is_open) WHERE is_open is not true; -- partial index, faster than full index


CREATE TABLE public.responses (
    response_id SERIAL PRIMARY KEY,
    phone_number text REFERENCES recipients (phone_number),
    item_id integer REFERENCES items (item_id),
    item_text text,
    created_datetime timestamp with time zone DEFAULT now(),
    opens_datetime timestamp with time zone,
    status_datetime timestamp with time zone DEFAULT now(),
    response integer,
    status text DEFAULT 'open'
);
ALTER TABLE public.responses OWNER TO postgres;


CREATE TABLE public.log (
    id SERIAL PRIMARY KEY,
    level character varying(10),
    message text,
    created_at timestamp without time zone DEFAULT now()
);
ALTER TABLE public.log OWNER TO postgres;


CREATE TABLE public.messages (
    sent_datetime timestamp with time zone DEFAULT now() NOT NULL,
    phone_number text REFERENCES recipients (phone_number),
    message_body text,
    direction text CHECK (direction IN ('outbound', 'inbound'))
);
ALTER TABLE public.messages OWNER TO postgres;

COMMENT ON TABLE public.messages IS 
'Holds all in- and outbound messages with timestamp, but without any tracking of which belong together. Table is meant for documentation and data scrutiny.';


-- INITIAL DATA

---- Instruments
INSERT INTO public.instruments (instrument_name, is_active) 
VALUES ('EQ-5D-5L', true);


---- Items
INSERT INTO public.items (instrument_id, item_text)
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
INSERT INTO public.recipients (phone_number, full_name) 
VALUES ('+4500000000', 'McUrl');

INSERT INTO public.iterations (instrument_id, phone_number, message_body, is_open, opens_datetime) 
SELECT
    1
    , phone_number
    , CONCAT('Dear ', full_name, '! Are you ready for another round? If so, reply with arbitrary messsage.')
    , true
    , now()
FROM public.recipients;

INSERT INTO responses (phone_number, item_text, item_id, opens_datetime, status)
SELECT
    '+4500000000'
    , item_text
    , item_id
    , now()
    , 'open'
FROM public.items;

INSERT INTO responses (phone_number, item_text, item_id, opens_datetime, status)
VALUES ('+4500000000', 'Thank you for your help! Reply with the word Restart to start over.', NULL, now(), 'open');
