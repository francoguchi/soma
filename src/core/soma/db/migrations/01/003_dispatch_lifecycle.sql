CREATE TABLE dispatch_locations (
 dispatch_location_id TEXT PRIMARY KEY,
 name TEXT NOT NULL CHECK(length(name)>0),
 name_match_key TEXT NOT NULL CHECK(length(name_match_key)>0),
 address_mode TEXT NOT NULL CHECK(address_mode IN ('standalone','site_derived')),
 standalone_address_text TEXT,
 lifecycle_state TEXT NOT NULL CHECK(lifecycle_state IN ('active','archived')),
 revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
 created_at_utc INTEGER NOT NULL CHECK(created_at_utc>=0),
 updated_at_utc INTEGER NOT NULL CHECK(updated_at_utc>=created_at_utc),
 CHECK((address_mode='standalone' AND standalone_address_text IS NOT NULL AND length(standalone_address_text)>0)
    OR (address_mode='site_derived' AND standalone_address_text IS NULL))
) STRICT;
CREATE INDEX idx_dispatch_active_name_match ON dispatch_locations(lifecycle_state,name_match_key,dispatch_location_id);
CREATE TRIGGER reference_dispatch_locations_update_guard BEFORE UPDATE ON dispatch_locations
WHEN NEW.dispatch_location_id IS NOT OLD.dispatch_location_id OR NEW.address_mode IS NOT OLD.address_mode
 OR NEW.created_at_utc IS NOT OLD.created_at_utc
 OR (NEW.address_mode='site_derived' AND NEW.standalone_address_text IS NOT NULL)
BEGIN SELECT RAISE(ABORT,'reference_dispatch_locations_update_guard'); END;
CREATE TRIGGER reference_dispatch_locations_delete_forbidden BEFORE DELETE ON dispatch_locations
BEGIN SELECT RAISE(ABORT,'reference_dispatch_locations_delete_forbidden'); END;
