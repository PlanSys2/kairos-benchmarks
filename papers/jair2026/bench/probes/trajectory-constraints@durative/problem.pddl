(define (problem tc1) (:domain tc) (:objects r1 - robot) (:init (ready r1))
 (:goal (and (b r1)))
 (:constraints (sometime-before (b r1) (a r1))))
