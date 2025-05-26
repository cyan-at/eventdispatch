Best practices
=====

* Events should only exist *as needed*
* Events should be *short-lived*
* Keep your Event definitions DRY, push as much variance into arguments
* **dispatch** level logic should be less volatile than **event** level logic

Patterns
=====

* Do prevent lost data: 'open the mouth before you feed it'
* To prevent lost data: 'buffer and drain'
* To deal with *temporal uncertainty*, dispatch sibling events together, and whichever one **finish**'s first, should cleanup its siblings
* To deal with *spatial* uncertainty, have the **event**(s) most collocated to the uncertainty handle it in their **finish** function(s)
