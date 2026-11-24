# hub.b: learnings

- Do not publish a price or offer until there is a way to take it up and the pricing pages agree (v0.1.43 was reverted).
- The link check fails a release on any 404: cite each source by its full address.
- Fetch sites.b's register with no cache (?t= and a no-cache header).
- Check a decision record's event_uuid in the session that recorded it (decisions.b's), not the conductor's.
- The live build runs about 30 to 60 px taller than a local one; keep each design about 100 px under 8,000 on a phone.
- Later @media blocks in tools/showroom/*.css can override earlier ones: check the computed value, not the edit.
- Say the address is the owner's only if they bring their own domain.
