(define (problem charger-5) (:domain charger) (:objects r1 r2 r3 r4 r5 - robot)
(:init (charger_free) (open) (free r1) (flat r1) (= (battery r1) 0) (= (capacity r1) 100) (= (need r1) 20) (free r2) (flat r2) (= (battery r2) 0) (= (capacity r2) 100) (= (need r2) 24) (free r3) (flat r3) (= (battery r3) 0) (= (capacity r3) 100) (= (need r3) 28) (free r4) (flat r4) (= (battery r4) 0) (= (capacity r4) 100) (= (need r4) 32) (free r5) (flat r5) (= (battery r5) 0) (= (capacity r5) 100) (= (need r5) 36) (at 46 (not (open))))
(:goal (and (done r1) (done r2) (done r3) (done r4) (done r5))))
