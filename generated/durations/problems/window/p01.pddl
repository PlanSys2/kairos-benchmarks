(define (problem window-1) (:domain window) (:objects r1 - robot)
(:init (open) (free r1) (can_charge r1) (= (battery r1) 10) (= (capacity r1) 100) (= (need r1) 26) (at 16 (not (open))))
(:goal (and (done r1))))
