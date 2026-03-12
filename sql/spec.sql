-- @block Add engine
insert into engines (id, name)
VALUES ('3fa85f64-5717-4562-b3fc-2c963f66afa6', 'test');
-- @block Add engine spec
INSERT INTO engine_specs (engine_id, config, enabled, generation)
VALUES (
        '3fa85f64-5717-4562-b3fc-2c963f66afa6',
        '{}',
        true,
        0
    );