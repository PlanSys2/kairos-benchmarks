(define (problem charger-3) (:domain charger) (:objects r1 r2 r3 - robot)
(:init (charger_free) (open) (free r1) (flat r1) (= (battery r1) 0) (= (capacity r1) 100) (= (need r1) 20) (free r2) (flat r2) (= (battery r2) 0) (= (capacity r2) 100) (= (need r2) 24) (free r3) (flat r3) (= (battery r3) 0) (= (capacity r3) 100) (= (need r3) 28) (at 25 (not (open))))
(:goal (and (done r1) (done r2) (done r3))))
