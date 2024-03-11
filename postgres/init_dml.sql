-- Instruments
INSERT INTO prod.instruments (instrument_name, is_active)
VALUES ('EQ-5D-5L', true);


-- Items
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


-- Dummy person, useful for cURL-based querying
INSERT INTO prod.recipients (phone_number, full_name)
VALUES ('4500000000', 'Test McUrl');

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
