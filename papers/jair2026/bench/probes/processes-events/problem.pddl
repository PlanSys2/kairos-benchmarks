(define (problem pe1) (:domain pe) (:objects r1 - robot) (:init (ready r1) (= (level r1) 0))
 (:goal (and (full r1) (not (overflow r1)))))
