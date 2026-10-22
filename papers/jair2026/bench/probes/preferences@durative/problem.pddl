(define (problem pr1) (:domain pr) (:objects r1 - robot) (:init (ready r1))
 (:goal (and (a r1) (preference pb (b r1))))
 (:metric minimize (is-violated pb)))
