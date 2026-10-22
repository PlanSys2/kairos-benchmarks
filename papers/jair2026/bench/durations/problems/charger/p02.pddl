(define (problem charger-2) (:domain charger) (:objects r1 r2 - robot)
(:init (charger_free) (open) (free r1) (flat r1) (= (battery r1) 0) (= (capacity r1) 100) (= (need r1) 20) (free r2) (flat r2) (= (battery r2) 0) (= (capacity r2) 100) (= (need r2) 24) (at 16 (not (open))))
(:goal (and (done r1) (done r2))))
