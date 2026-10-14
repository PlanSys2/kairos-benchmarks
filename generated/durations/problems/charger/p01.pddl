(define (problem charger-1) (:domain charger) (:objects r1 - robot)
(:init (charger_free) (open) (free r1) (flat r1) (= (battery r1) 0) (= (capacity r1) 100) (= (need r1) 20) (at 8 (not (open))))
(:goal (and (done r1))))
