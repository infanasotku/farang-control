-- @block Get state
SELECT *
FROM engine_runtime_states
WHERE engine_id = '3fa85f64-5717-4562-b3fc-2c963f66afa6';
-- @block Get instances by engine id
SELECT *
FROM engine_instances
WHERE engine_id = '3fa85f64-5717-4562-b3fc-2c963f66afa6';