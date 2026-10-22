(define (problem window-2) (:domain window) (:objects r1 r2 - robot)
(:init (open) (free r1) (can_charge r1) (= (battery r1) 10) (= (capacity r1) 100) (= (need r1) 26) (free r2) (can_charge r2) (= (battery r2) 10) (= (capacity r2) 100) (= (need r2) 28) (at 17 (not (open))))
(:goal (and (done r1) (done r2))))
